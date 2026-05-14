"""
Pattern Similarity — Explainable episode-to-episode similarity scoring.

Computes multi-factor similarity between SensorEpisodes, producing a
``SimilarityResult`` that enumerates every contributing factor and its
weight so downstream consumers can understand *why* two episodes matched.

Also provides single-linkage clustering via ``find_clusters``.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from memory.somatic.environmental_signature import EnvironmentalSignature
from memory.somatic.anomaly_fingerprint import AnomalyFingerprint


# ── Result types ──────────────────────────────────────────────────────────


@dataclass
class SimilarityResult:
    """Outcome of comparing two episodes."""

    score: float = 0.0
    factors: dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "explanation": self.explanation,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class EpisodeCluster:
    """A group of similar episodes."""

    cluster_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    episode_ids: list[str] = field(default_factory=list)
    centroid_episode_id: str = ""
    avg_similarity: float = 0.0
    pattern_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "episode_ids": self.episode_ids,
            "centroid_episode_id": self.centroid_episode_id,
            "avg_similarity": round(self.avg_similarity, 4),
            "pattern_description": self.pattern_description,
        }


# ── Factor weights ────────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "signal_type_overlap": 0.25,
    "env_distance": 0.20,
    "severity_similarity": 0.20,
    "temporal_similarity": 0.15,
    "fingerprint_match": 0.20,
}


# ── PatternSimilarity engine ─────────────────────────────────────────────


class PatternSimilarity:
    """Stateless engine for computing episode similarity."""

    def __init__(self, weights: dict[str, float] | None = None):
        self._weights = weights or dict(_WEIGHTS)

    def episode_similarity(
        self,
        a: Any,  # SensorEpisode (Any to avoid circular import at module level)
        b: Any,
    ) -> SimilarityResult:
        factors: dict[str, float] = {}

        # 1. Signal type overlap (Jaccard)
        set_a = set(a.signal_types) if a.signal_types else set()
        set_b = set(b.signal_types) if b.signal_types else set()
        if set_a or set_b:
            jaccard = len(set_a & set_b) / len(set_a | set_b)
        else:
            jaccard = 1.0
        factors["signal_type_overlap"] = jaccard

        # 2. Environmental distance
        env_a = EnvironmentalSignature.from_dict(a.environmental_signature) if a.environmental_signature else EnvironmentalSignature()
        env_b = EnvironmentalSignature.from_dict(b.environmental_signature) if b.environmental_signature else EnvironmentalSignature()
        env_dist = env_a.distance_to(env_b)
        factors["env_distance"] = 1.0 - env_dist

        # 3. Severity similarity
        sev_diff = abs(a.severity_peak - b.severity_peak)
        factors["severity_similarity"] = 1.0 - min(sev_diff, 1.0)

        # 4. Temporal similarity (duration + time-of-day)
        factors["temporal_similarity"] = self._temporal_similarity(a, b)

        # 5. Fingerprint match
        if a.fingerprint and b.fingerprint:
            fp_a = AnomalyFingerprint.from_dict({"fingerprint_id": a.fingerprint, "signal_pattern": "+".join(a.signal_types)})
            fp_b = AnomalyFingerprint.from_dict({"fingerprint_id": b.fingerprint, "signal_pattern": "+".join(b.signal_types)})
            factors["fingerprint_match"] = fp_a.match(fp_b)
        else:
            factors["fingerprint_match"] = factors["signal_type_overlap"]

        weighted_sum = sum(
            factors.get(k, 0.0) * w for k, w in self._weights.items()
        )
        score = min(weighted_sum, 1.0)

        non_zero = sum(1 for v in factors.values() if v > 0.1)
        confidence = min(non_zero / len(factors), 1.0) if factors else 0.0

        explanation = self._explain(factors, score)

        return SimilarityResult(
            score=score,
            factors=factors,
            explanation=explanation,
            confidence=confidence,
        )

    def find_clusters(
        self,
        episodes: list[Any],
        threshold: float = 0.5,
    ) -> list[EpisodeCluster]:
        """Single-linkage clustering: merge episodes whose pairwise
        similarity exceeds *threshold*."""
        n = len(episodes)
        if n == 0:
            return []

        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        sim_cache: dict[tuple[int, int], float] = {}
        for i in range(n):
            for j in range(i + 1, n):
                result = self.episode_similarity(episodes[i], episodes[j])
                sim_cache[(i, j)] = result.score
                if result.score >= threshold:
                    union(i, j)

        groups: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            groups.setdefault(root, []).append(i)

        clusters: list[EpisodeCluster] = []
        for members in groups.values():
            if len(members) < 2:
                continue

            pair_sims: list[float] = []
            for i_idx, i in enumerate(members):
                for j in members[i_idx + 1:]:
                    key = (min(i, j), max(i, j))
                    pair_sims.append(sim_cache.get(key, 0.0))
            avg_sim = sum(pair_sims) / len(pair_sims) if pair_sims else 0.0

            best_idx = members[0]
            best_total = 0.0
            for i in members:
                total = sum(
                    sim_cache.get((min(i, j), max(i, j)), 0.0)
                    for j in members if j != i
                )
                if total > best_total:
                    best_total = total
                    best_idx = i

            ep_ids = [episodes[i].episode_id for i in members]
            types_union: set[str] = set()
            for i in members:
                types_union.update(episodes[i].signal_types)
            desc = f"Cluster of {len(members)} episodes: " + "+".join(sorted(types_union))

            clusters.append(EpisodeCluster(
                episode_ids=ep_ids,
                centroid_episode_id=episodes[best_idx].episode_id,
                avg_similarity=avg_sim,
                pattern_description=desc,
            ))

        return clusters

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _temporal_similarity(a: Any, b: Any) -> float:
        dur_sim = 1.0
        if a.duration_ms > 0 and b.duration_ms > 0:
            ratio = min(a.duration_ms, b.duration_ms) / max(a.duration_ms, b.duration_ms)
            dur_sim = ratio

        tod_sim = 1.0
        try:
            hour_a = a.timestamp.hour + a.timestamp.minute / 60.0
            hour_b = b.timestamp.hour + b.timestamp.minute / 60.0
            hour_diff = abs(hour_a - hour_b)
            hour_diff = min(hour_diff, 24.0 - hour_diff)
            tod_sim = 1.0 - (hour_diff / 12.0)
        except AttributeError:
            pass

        return dur_sim * 0.5 + tod_sim * 0.5

    @staticmethod
    def _explain(factors: dict[str, float], score: float) -> str:
        parts: list[str] = []
        for name, value in sorted(factors.items(), key=lambda t: t[1], reverse=True):
            if value >= 0.8:
                parts.append(f"{name}: strong ({value:.0%})")
            elif value >= 0.4:
                parts.append(f"{name}: moderate ({value:.0%})")
            elif value > 0.05:
                parts.append(f"{name}: weak ({value:.0%})")
        if not parts:
            return f"Overall similarity {score:.0%} — no strong contributing factors"
        return f"Overall similarity {score:.0%} — " + "; ".join(parts)
