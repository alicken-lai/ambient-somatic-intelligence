"""Assign somatic episodes to ontology-aware clusters.

Extends the existing PatternSimilarity clustering with ontology
awareness so that every cluster assignment tracks which ontology
layer the cluster maps to, and clusters can be evaluated for
promotion to higher layers.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ClusterAssignment:
    """Records the assignment of an episode to a cluster."""

    episode_id: str
    cluster_id: str
    assignment_confidence: float
    assigned_at: datetime = field(default_factory=_utc_now)
    ontology_layer: int = 1  # which layer this cluster maps to

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "cluster_id": self.cluster_id,
            "assignment_confidence": round(self.assignment_confidence, 6),
            "assigned_at": self.assigned_at.isoformat(),
            "ontology_layer": self.ontology_layer,
        }


class OntologyAwareClusterer:
    """Extends PatternSimilarity clustering with ontology awareness.

    Uses the similarity engine to score episodes against existing
    clusters, and the ontology bridge to check / propose promotions.
    """

    def __init__(self, similarity_engine: Any, bridge: Any):
        self._sim = similarity_engine
        self._bridge = bridge

    def assign_to_cluster(
        self,
        episode: Any,
        existing_clusters: list[Any],
    ) -> ClusterAssignment:
        """Assign episode to the best matching cluster, or create a new one.

        Scores the episode against each cluster's centroid episode.
        If no cluster exceeds a 0.5 similarity threshold a new
        single-episode cluster is created at L1.
        """
        best_cluster: Any = None
        best_score: float = 0.0

        for cluster in existing_clusters:
            if not cluster.centroid_episode_id:
                continue
            result = self._sim.episode_similarity(episode, _CentroidProxy(cluster))
            if result.score > best_score:
                best_score = result.score
                best_cluster = cluster

        if best_cluster is not None and best_score >= 0.5:
            ontology_layer = self._resolve_layer(best_cluster)
            return ClusterAssignment(
                episode_id=episode.episode_id,
                cluster_id=best_cluster.cluster_id,
                assignment_confidence=best_score,
                ontology_layer=ontology_layer,
            )

        new_id = uuid.uuid4().hex[:12]
        return ClusterAssignment(
            episode_id=episode.episode_id,
            cluster_id=new_id,
            assignment_confidence=1.0,
            ontology_layer=1,
        )

    def evaluate_cluster_promotion(self, cluster: Any) -> Optional[dict[str, Any]]:
        """Check if a cluster is ready for promotion to the next layer.

        Returns a promotion proposal dict, or None if not ready.
        Thresholds:
          - L1→L2: >= 3 episodes
          - L2→L3: >= 5 episodes and avg_similarity >= 0.7
          - L3→L4: >= 10 episodes and avg_similarity >= 0.85
        """
        ep_count = len(cluster.episode_ids)
        current_layer = self._resolve_layer(cluster)

        if current_layer == 1 and ep_count >= 3:
            return {
                "cluster_id": cluster.cluster_id,
                "current_layer": 1,
                "proposed_layer": 2,
                "episode_count": ep_count,
                "avg_similarity": cluster.avg_similarity,
                "requires_governance": True,
            }
        if current_layer == 2 and ep_count >= 5 and cluster.avg_similarity >= 0.7:
            return {
                "cluster_id": cluster.cluster_id,
                "current_layer": 2,
                "proposed_layer": 3,
                "episode_count": ep_count,
                "avg_similarity": cluster.avg_similarity,
                "requires_governance": True,
            }
        if current_layer == 3 and ep_count >= 10 and cluster.avg_similarity >= 0.85:
            return {
                "cluster_id": cluster.cluster_id,
                "current_layer": 3,
                "proposed_layer": 4,
                "episode_count": ep_count,
                "avg_similarity": cluster.avg_similarity,
                "requires_governance": True,
            }
        return None

    def cross_project_similarity(
        self,
        cluster: Any,
        external_patterns: list[dict[str, Any]],
    ) -> float:
        """Score similarity with patterns from other contexts.

        Compares the cluster's pattern description and signal types
        against each external pattern's fields.  Returns the highest
        Jaccard overlap found, or 0.0 if no overlap.
        """
        if not external_patterns:
            return 0.0

        cluster_types: set[str] = set()
        desc = getattr(cluster, "pattern_description", "")
        if desc:
            for part in desc.split(":"):
                for token in part.split("+"):
                    token = token.strip().lower()
                    if token and not token.startswith("cluster"):
                        cluster_types.add(token)

        best = 0.0
        for ext in external_patterns:
            ext_types = {t.lower() for t in ext.get("signal_types", [])}
            if not cluster_types and not ext_types:
                continue
            union = cluster_types | ext_types
            if union:
                jaccard = len(cluster_types & ext_types) / len(union)
                best = max(best, jaccard)
        return best

    # ── Helpers ───────────────────────────────────────────────────────

    def _resolve_layer(self, cluster: Any) -> int:
        """Determine the current ontology layer for a cluster."""
        mappings = self._bridge.get_mappings_by_layer(3)
        for m in mappings:
            if m.source_id == cluster.cluster_id:
                return 3
        mappings_l2 = self._bridge.get_mappings_by_layer(2)
        for m in mappings_l2:
            if m.source_id == cluster.cluster_id:
                return 2
        return 1


class _CentroidProxy:
    """Lightweight proxy so the similarity engine can compare against a cluster centroid."""

    def __init__(self, cluster: Any):
        self.episode_id = cluster.centroid_episode_id
        self.signal_types = self._extract_types(cluster)
        self.environmental_signature: dict[str, Any] = {}
        self.severity_peak: float = 0.0
        self.duration_ms: float = 0.0
        self.timestamp = _utc_now()
        self.fingerprint = ""

    @staticmethod
    def _extract_types(cluster: Any) -> list[str]:
        desc = getattr(cluster, "pattern_description", "")
        if ":" in desc:
            types_part = desc.split(":")[-1].strip()
            return [t.strip().lower() for t in types_part.split("+") if t.strip()]
        return []
