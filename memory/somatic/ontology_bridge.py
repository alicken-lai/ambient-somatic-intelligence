"""Bridge between somatic episodes and the memory ontology layers.

Maps somatic data to the formal L1–L4 memory hierarchy:
  - SensorEpisode      → L1 (Episodic)
  - AnomalyFingerprint → L2 (Instinct) candidates
  - EpisodeCluster     → L3 (Skill) candidates
  - Precursor patterns → L4 (Strategic) candidates

Every promotion beyond L1 requires governance approval.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return _utc_now()


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass
class OntologyMapping:
    """Maps a somatic entity to its ontology layer position."""

    source_id: str
    source_type: str  # "episode", "fingerprint", "cluster", "precursor"
    target_layer: int  # 1, 2, 3, or 4
    target_entry_id: str
    confidence: float
    mapped_at: datetime
    mapping_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "target_layer": self.target_layer,
            "target_entry_id": self.target_entry_id,
            "confidence": round(self.confidence, 6),
            "mapped_at": self.mapped_at.isoformat(),
            "mapping_reason": self.mapping_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OntologyMapping:
        return cls(
            source_id=data["source_id"],
            source_type=data["source_type"],
            target_layer=int(data["target_layer"]),
            target_entry_id=data["target_entry_id"],
            confidence=float(data.get("confidence", 0.0)),
            mapped_at=_parse_dt(data.get("mapped_at")),
            mapping_reason=data.get("mapping_reason", ""),
        )


@dataclass
class PromotionCandidate:
    """A somatic entity that may be promoted to a higher ontology layer."""

    source_id: str
    source_type: str
    current_layer: int
    proposed_layer: int
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)
    requires_governance: bool = True
    proposed_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "current_layer": self.current_layer,
            "proposed_layer": self.proposed_layer,
            "confidence": round(self.confidence, 6),
            "evidence": self.evidence,
            "requires_governance": self.requires_governance,
            "proposed_at": self.proposed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromotionCandidate:
        return cls(
            source_id=data["source_id"],
            source_type=data["source_type"],
            current_layer=int(data["current_layer"]),
            proposed_layer=int(data["proposed_layer"]),
            confidence=float(data.get("confidence", 0.0)),
            evidence=data.get("evidence", {}),
            requires_governance=data.get("requires_governance", True),
            proposed_at=_parse_dt(data.get("proposed_at")),
        )


# ── Bridge ────────────────────────────────────────────────────────────────


class SomaticOntologyBridge:
    """Bridges somatic memory to the formal ontology.

    All mappings are persisted to a JSONL file and every promotion
    beyond L1 is flagged for governance review.
    """

    def __init__(self, mappings_path: str = "memory/somatic/ontology_mappings.jsonl"):
        self._mappings: list[OntologyMapping] = []
        self._candidates: list[PromotionCandidate] = []
        self._mappings_path = Path(mappings_path)
        self._load()

    # ── Mapping helpers ───────────────────────────────────────────────

    def map_episode_to_l1(self, episode: Any) -> OntologyMapping:
        """Map a SensorEpisode to L1 Episodic layer.

        Episodes are always L1 — raw environmental data that does not
        require governance approval.
        """
        entry_id = f"L1-{episode.episode_id}"
        mapping = OntologyMapping(
            source_id=episode.episode_id,
            source_type="episode",
            target_layer=1,
            target_entry_id=entry_id,
            confidence=1.0,
            mapped_at=_utc_now(),
            mapping_reason="Direct episode → L1 episodic mapping",
        )
        self._mappings.append(mapping)
        self._save()
        return mapping

    def map_fingerprint_to_l2(
        self,
        fingerprint: Any,
        min_occurrences: int = 3,
    ) -> Optional[OntologyMapping]:
        """Map an AnomalyFingerprint to L2 Instinct if it meets occurrence threshold."""
        if fingerprint.occurrence_count < min_occurrences:
            return None

        entry_id = f"L2-{fingerprint.fingerprint_id}"
        confidence = min(fingerprint.occurrence_count / (min_occurrences * 3), 0.99)
        mapping = OntologyMapping(
            source_id=fingerprint.fingerprint_id,
            source_type="fingerprint",
            target_layer=2,
            target_entry_id=entry_id,
            confidence=confidence,
            mapped_at=_utc_now(),
            mapping_reason=(
                f"Fingerprint has {fingerprint.occurrence_count} occurrences "
                f"(threshold={min_occurrences})"
            ),
        )
        self._mappings.append(mapping)
        self._save()
        return mapping

    def map_cluster_to_l3(
        self,
        cluster: Any,
        min_episodes: int = 5,
        min_similarity: float = 0.7,
    ) -> Optional[OntologyMapping]:
        """Map an EpisodeCluster to L3 Skill if it represents a reusable pattern."""
        episode_count = len(cluster.episode_ids)
        if episode_count < min_episodes:
            return None
        if cluster.avg_similarity < min_similarity:
            return None

        entry_id = f"L3-{cluster.cluster_id}"
        confidence = min(
            (cluster.avg_similarity * 0.6) + (min(episode_count / 20, 1.0) * 0.4),
            0.99,
        )
        mapping = OntologyMapping(
            source_id=cluster.cluster_id,
            source_type="cluster",
            target_layer=3,
            target_entry_id=entry_id,
            confidence=confidence,
            mapped_at=_utc_now(),
            mapping_reason=(
                f"Cluster with {episode_count} episodes, "
                f"avg_similarity={cluster.avg_similarity:.3f}"
            ),
        )
        self._mappings.append(mapping)
        self._save()
        return mapping

    def propose_escalation_strategy(
        self,
        precursor_pattern: Any,
        min_confidence: float = 0.8,
    ) -> Optional[PromotionCandidate]:
        """Propose a precursor pattern as L4 Strategic candidate.

        Strategic promotion always requires governance — no auto-promotion.
        """
        if precursor_pattern.confidence < min_confidence:
            return None

        candidate = PromotionCandidate(
            source_id=precursor_pattern.pattern_id,
            source_type="precursor",
            current_layer=2,
            proposed_layer=4,
            confidence=precursor_pattern.confidence,
            evidence={
                "support_count": precursor_pattern.support_count,
                "avg_lead_time_seconds": precursor_pattern.avg_lead_time_seconds,
                "target_event_type": precursor_pattern.target_event_type,
                "precursor_signals": precursor_pattern.precursor_signals,
            },
            requires_governance=True,
            proposed_at=_utc_now(),
        )
        self._candidates.append(candidate)
        self._save()
        return candidate

    # ── Scanning ──────────────────────────────────────────────────────

    def scan_promotion_candidates(
        self,
        episodes: list[Any],
        fingerprints: list[Any],
        clusters: list[Any],
        precursors: list[Any],
    ) -> list[PromotionCandidate]:
        """Scan all somatic entities for promotion candidates."""
        candidates: list[PromotionCandidate] = []

        for fp in fingerprints:
            if fp.occurrence_count >= 3:
                candidates.append(PromotionCandidate(
                    source_id=fp.fingerprint_id,
                    source_type="fingerprint",
                    current_layer=1,
                    proposed_layer=2,
                    confidence=min(fp.occurrence_count / 9.0, 0.99),
                    evidence={
                        "occurrence_count": fp.occurrence_count,
                        "severity_band": fp.severity_band,
                    },
                    requires_governance=True,
                ))

        for cluster in clusters:
            ep_count = len(cluster.episode_ids)
            if ep_count >= 5 and cluster.avg_similarity >= 0.7:
                candidates.append(PromotionCandidate(
                    source_id=cluster.cluster_id,
                    source_type="cluster",
                    current_layer=2,
                    proposed_layer=3,
                    confidence=min(
                        (cluster.avg_similarity * 0.6) + (min(ep_count / 20, 1.0) * 0.4),
                        0.99,
                    ),
                    evidence={
                        "episode_count": ep_count,
                        "avg_similarity": cluster.avg_similarity,
                    },
                    requires_governance=True,
                ))

        for precursor in precursors:
            if precursor.confidence >= 0.8:
                candidates.append(PromotionCandidate(
                    source_id=precursor.pattern_id,
                    source_type="precursor",
                    current_layer=2,
                    proposed_layer=4,
                    confidence=precursor.confidence,
                    evidence={
                        "support_count": precursor.support_count,
                        "target_event_type": precursor.target_event_type,
                    },
                    requires_governance=True,
                ))

        self._candidates.extend(candidates)
        self._save()
        return candidates

    # ── Confidence updates ────────────────────────────────────────────

    def update_confidence(self, source_id: str, success: bool) -> float:
        """Update confidence for a mapped entity based on outcome.

        Success: conf + 0.05 * (1 - conf)
        Failure: conf - 0.1 * conf, floor 0.01
        """
        for mapping in self._mappings:
            if mapping.source_id == source_id:
                if success:
                    mapping.confidence = min(
                        mapping.confidence + 0.05 * (1.0 - mapping.confidence),
                        0.99,
                    )
                else:
                    mapping.confidence = max(
                        mapping.confidence - 0.1 * mapping.confidence,
                        0.01,
                    )
                self._save()
                return mapping.confidence
        return 0.0

    # ── Queries ───────────────────────────────────────────────────────

    def get_mappings_by_layer(self, layer: int) -> list[OntologyMapping]:
        """Get all somatic→ontology mappings for a given layer."""
        return [m for m in self._mappings if m.target_layer == layer]

    # ── Persistence ───────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._mappings_path.exists():
            return
        try:
            with self._mappings_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        kind = data.get("_kind")
                        if kind == "mapping":
                            self._mappings.append(OntologyMapping.from_dict(data))
                        elif kind == "candidate":
                            self._candidates.append(PromotionCandidate.from_dict(data))
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.warning("Skipped malformed ontology line: %s", exc)
        except OSError as exc:
            logger.error("Failed to load ontology mappings: %s", exc)

    def _save(self) -> None:
        self._mappings_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._mappings_path.open("w", encoding="utf-8") as fh:
                for m in self._mappings:
                    record = m.to_dict()
                    record["_kind"] = "mapping"
                    fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                for c in self._candidates:
                    record = c.to_dict()
                    record["_kind"] = "candidate"
                    fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            logger.error("Failed to save ontology mappings: %s", exc)

    # ── Audit ─────────────────────────────────────────────────────────

    def to_audit_report(self) -> str:
        """Human-readable audit report of all mappings and candidates."""
        lines: list[str] = ["=== Somatic → Ontology Audit Report ===", ""]

        for layer in (1, 2, 3, 4):
            layer_maps = self.get_mappings_by_layer(layer)
            lines.append(f"--- Layer {layer} ({len(layer_maps)} mappings) ---")
            for m in layer_maps:
                lines.append(
                    f"  {m.source_type}:{m.source_id} → {m.target_entry_id} "
                    f"(confidence={m.confidence:.3f}, reason={m.mapping_reason!r})"
                )
            lines.append("")

        if self._candidates:
            lines.append(f"--- Promotion Candidates ({len(self._candidates)}) ---")
            for c in self._candidates:
                gov = "GOVERNANCE REQUIRED" if c.requires_governance else "auto"
                lines.append(
                    f"  {c.source_type}:{c.source_id} L{c.current_layer}→L{c.proposed_layer} "
                    f"(confidence={c.confidence:.3f}, {gov})"
                )

        return "\n".join(lines)
