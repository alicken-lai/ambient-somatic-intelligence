"""
Workflow Cluster — Cluster similar workflow patterns for skill extraction.

Groups related WorkflowPatterns by step-sequence overlap, schema similarity,
and governance requirements. Each cluster is scored for skill_potential to
guide candidate generation priority.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from agents.skillify.pattern_miner import WorkflowPattern

logger = logging.getLogger(__name__)


@dataclass
class WorkflowClusterGroup:
    """A cluster of related workflow patterns."""
    cluster_id: str
    patterns: list[WorkflowPattern]
    representative: WorkflowPattern
    similarity_matrix: dict[str, float]
    skill_potential: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "patterns": [p.to_dict() for p in self.patterns],
            "representative": self.representative.to_dict(),
            "similarity_matrix": self.similarity_matrix,
            "skill_potential": round(self.skill_potential, 3),
        }


class WorkflowCluster:
    """
    Cluster similar workflow patterns for skill candidate generation.

    Similarity is computed from three dimensions:
      - Step sequence overlap (Jaccard)
      - Input/output schema overlap (Jaccard)
      - Governance requirements match (exact)

    Usage:
        clusterer = WorkflowCluster()
        groups = clusterer.cluster(patterns, threshold=0.7)
    """

    def cluster(
        self,
        patterns: list[WorkflowPattern],
        threshold: float = 0.7,
    ) -> list[WorkflowClusterGroup]:
        """
        Cluster patterns whose pairwise similarity exceeds threshold.

        Uses single-linkage: a pattern joins a cluster if it is similar
        enough to *any* existing member.
        """
        if not patterns:
            return []

        sim_cache: dict[tuple[str, str], float] = {}
        for i, a in enumerate(patterns):
            for b in patterns[i + 1:]:
                score = self._similarity(a, b)
                sim_cache[(a.pattern_id, b.pattern_id)] = score
                sim_cache[(b.pattern_id, a.pattern_id)] = score

        assigned: set[str] = set()
        groups: list[WorkflowClusterGroup] = []

        sorted_patterns = sorted(
            patterns,
            key=lambda p: (p.success_rate, p.occurrence_count),
            reverse=True,
        )

        for seed in sorted_patterns:
            if seed.pattern_id in assigned:
                continue

            cluster_members = [seed]
            assigned.add(seed.pattern_id)

            for candidate in sorted_patterns:
                if candidate.pattern_id in assigned:
                    continue
                for member in cluster_members:
                    pair = (member.pattern_id, candidate.pattern_id)
                    if sim_cache.get(pair, 0.0) >= threshold:
                        cluster_members.append(candidate)
                        assigned.add(candidate.pattern_id)
                        break

            sim_matrix: dict[str, float] = {}
            for i, a in enumerate(cluster_members):
                for b in cluster_members[i + 1:]:
                    key = f"{a.pattern_id}:{b.pattern_id}"
                    sim_matrix[key] = sim_cache.get(
                        (a.pattern_id, b.pattern_id), 0.0
                    )

            representative = max(
                cluster_members,
                key=lambda p: (p.occurrence_count, p.success_rate),
            )
            skill_potential = self._compute_skill_potential(cluster_members)

            groups.append(WorkflowClusterGroup(
                cluster_id=f"wc-{uuid.uuid4().hex[:8]}",
                patterns=cluster_members,
                representative=representative,
                similarity_matrix=sim_matrix,
                skill_potential=skill_potential,
            ))

        groups.sort(key=lambda g: g.skill_potential, reverse=True)
        logger.info(
            "Clustered %d patterns into %d groups (threshold=%.2f)",
            len(patterns), len(groups), threshold,
        )
        return groups

    def _similarity(self, a: WorkflowPattern, b: WorkflowPattern) -> float:
        """Compute composite similarity between two patterns."""
        step_sim = self._jaccard(set(a.canonical_steps), set(b.canonical_steps))
        input_sim = self._jaccard(set(a.input_schema.keys()), set(b.input_schema.keys()))
        output_sim = self._jaccard(set(a.output_schema.keys()), set(b.output_schema.keys()))
        gov_sim = self._jaccard(set(a.governance_requirements), set(b.governance_requirements))

        schema_sim = (input_sim + output_sim) / 2.0

        return 0.5 * step_sim + 0.3 * schema_sim + 0.2 * gov_sim

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> float:
        """Jaccard similarity between two sets."""
        if not a and not b:
            return 1.0
        union = a | b
        if not union:
            return 0.0
        return len(a & b) / len(union)

    def _compute_skill_potential(self, members: list[WorkflowPattern]) -> float:
        """
        Score how suitable a cluster is for becoming a skill (0.0-1.0).

        Factors:
          - High total occurrence count
          - High average success rate
          - Low variation (consistent behavior)
          - Multiple patterns (broader applicability)
        """
        if not members:
            return 0.0

        total_occurrences = sum(m.occurrence_count for m in members)
        avg_success = sum(m.success_rate for m in members) / len(members)
        avg_variation = sum(m.variation_score for m in members) / len(members)

        occurrence_score = min(total_occurrences / 20.0, 1.0)
        success_score = avg_success
        consistency_score = 1.0 - avg_variation
        breadth_score = min(len(members) / 5.0, 1.0)

        potential = (
            0.3 * occurrence_score
            + 0.35 * success_score
            + 0.2 * consistency_score
            + 0.15 * breadth_score
        )
        return round(min(potential, 1.0), 3)
