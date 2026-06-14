"""Small queryable deliberation knowledge graph."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class DeliberationKnowledgeGraph:
    def __init__(self):
        self.edges: dict[str, list[dict[str, str]]] = defaultdict(list)

    def add_edge(self, source: str, relation: str, target: str) -> None:
        edge = {"relation": relation, "target": target}
        if edge not in self.edges[source]:
            self.edges[source].append(edge)

    def build(self, *, skills: list[Any], playbooks: list[Any], failures: list[dict[str, Any]]) -> "DeliberationKnowledgeGraph":
        for skill in skills:
            for task_type in skill.task_types:
                self.add_edge(task_type, "uses_skill", skill.skill_id)
        for playbook in playbooks:
            for task_type in playbook.task_types:
                self.add_edge(task_type, "uses_playbook", playbook.playbook_id)
            for child in playbook.recommended_children:
                self.add_edge(playbook.playbook_id, "selects_child", child)
        for failure in failures:
            self.add_edge(failure["failure_type"], "mitigated_by", failure["recommended_fix"])
        return self

    def add_acquisition_assets(
        self,
        *,
        evidence_sources: list[Any],
        knowledge_assets: list[Any],
        confidence_scores: dict[str, float],
        reuse_events: list[dict[str, Any]],
    ) -> "DeliberationKnowledgeGraph":
        for source in evidence_sources:
            self.add_edge("EvidenceSources", "contains", source.source_id)
        for asset in knowledge_assets:
            asset_id = asset.get("id") or asset.get("skill_id") or asset.get("playbook_id") or asset.get("item_id") or "unknown_asset"
            self.add_edge("KnowledgeAssets", "contains", str(asset_id))
        for item_id, score in confidence_scores.items():
            self.add_edge(str(item_id), "has_confidence", str(score))
        for event in reuse_events:
            claim_id = event.get("claim_id", "unknown_claim")
            self.add_edge(str(claim_id), "has_reuse_event", str(event.get("reuse_frequency", 0)))
        return self

    def add_calibration_assets(
        self,
        *,
        trust_records: list[Any],
        confidence_nodes: dict[str, float],
        drift_events: list[dict[str, Any]],
        inflation_events: list[dict[str, Any]],
        reliability_history: list[dict[str, Any]],
    ) -> "DeliberationKnowledgeGraph":
        for record in trust_records:
            self.add_edge(record.entity_id, "has_trust", record.trust_id)
        for entity_id, score in confidence_nodes.items():
            self.add_edge(entity_id, "has_calibrated_confidence", str(score))
        for event in drift_events:
            self.add_edge("DriftEvents", "contains", str(event))
        for event in inflation_events:
            self.add_edge("InflationEvents", "contains", str(event))
        for event in reliability_history:
            self.add_edge("ReliabilityHistory", "contains", str(event))
        return self

    def add_reality_alignment_assets(
        self,
        *,
        beliefs: dict[str, Any],
        reality_scores: dict[str, dict[str, Any]],
        fitness_scores: list[dict[str, Any]],
        challenge_events: list[dict[str, Any]],
        diversity_metrics: dict[str, Any],
        validation_outcomes: list[dict[str, Any]] | None = None,
    ) -> "DeliberationKnowledgeGraph":
        for belief_id, belief in beliefs.items():
            target_id = belief.get("source_target_id") or belief_id
            self.add_edge("Beliefs", "contains", belief_id)
            self.add_edge(belief_id, "tracks_target", str(target_id))
        for target_id, score in reality_scores.items():
            self.add_edge(str(target_id), "has_reality_score", str(score.get("reality_score", 0.0)))
        for fitness in fitness_scores:
            self.add_edge(str(fitness.get("target_id")), "has_fitness_score", str(fitness.get("fitness_score", 0.0)))
        for event in challenge_events:
            self.add_edge(str(event.get("target_id")), "has_challenge_event", str(event.get("challenge_id")))
        self.add_edge("DiversityMetrics", "has_diversity_score", str(diversity_metrics.get("diversity_score", 0.0)))
        for outcome in validation_outcomes or []:
            self.add_edge(str(outcome.get("target_id")), "has_validation_outcome", str(outcome.get("outcome_id")))
        return self

    def trust_weighted_query(self, source: str, trust_scores: dict[str, float], *, minimum_trust: float = 0.5) -> list[dict[str, str]]:
        return [
            edge
            for edge in self.query(source)
            if trust_scores.get(edge["target"], trust_scores.get(source, 1.0)) >= minimum_trust
        ]

    def query(self, source: str, relation: str | None = None) -> list[dict[str, str]]:
        edges = list(self.edges.get(source, []))
        if relation is None:
            return edges
        return [edge for edge in edges if edge["relation"] == relation]

    def best_playbook_for(self, task_type: str) -> str | None:
        playbooks = self.query(task_type, "uses_playbook")
        return playbooks[0]["target"] if playbooks else None
