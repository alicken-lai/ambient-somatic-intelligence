"""Reality alignment orchestration."""

from __future__ import annotations

from typing import Any

from hermes.calibration.reports import build_calibration_assets
from hermes.deliberation.evaluation.knowledge_reports import build_knowledge_assets
from hermes.reality_alignment.belief_evolution import evolve_beliefs
from hermes.reality_alignment.belief_registry import BeliefRegistry
from hermes.reality_alignment.challenge_engine import RealityChallengeEngine
from hermes.reality_alignment.echo_chamber_detector import detect_echo_chamber
from hermes.reality_alignment.fitness_engine import FitnessEngine
from hermes.reality_alignment.knowledge_diversity import measure_knowledge_diversity
from hermes.reality_alignment.reality_models import RealityObservation, RealityTarget
from hermes.reality_alignment.reality_score import compute_reality_score


class RealityAlignmentEngine:
    def __init__(self, belief_registry: BeliefRegistry | None = None):
        self.belief_registry = belief_registry or BeliefRegistry()

    def build_targets(self) -> list[RealityTarget]:
        calibration = build_calibration_assets()
        knowledge = build_knowledge_assets()
        targets: list[RealityTarget] = []
        for record in calibration["trust_records"]:
            targets.append(
                RealityTarget(
                    target_id=record.entity_id,
                    target_type=record.entity_type,
                    statement=f"{record.entity_type} {record.entity_id} remains trustworthy for institutional reuse",
                    confidence=calibration["confidence"]["overall"] / 100.0,
                    trust_score=record.trust_score,
                    verification_success=calibration["confidence"]["verification"] / 100.0,
                    historical_quality=calibration["health"]["health_score"] / 100.0,
                    outcome_quality=calibration["confidence"]["consistency"] / 100.0,
                    sources=[record.entity_id, "reports/trust_registry.json"],
                    internal_sources=[record.entity_id, "reports/trust_registry.json"],
                )
            )
        for playbook in knowledge["playbooks"].values():
            targets.append(
                RealityTarget(
                    target_id=playbook.playbook_id,
                    target_type="playbook",
                    statement=f"Playbook {playbook.name} improves task quality",
                    confidence=max(playbook.success_rate, 0.65),
                    trust_score=max(playbook.success_rate, 0.6),
                    verification_success=1.0 if playbook.success_criteria else 0.5,
                    historical_quality=playbook.success_rate,
                    outcome_quality=max(0.0, min(1.0, playbook.average_roi or playbook.success_rate)),
                    sources=[playbook.playbook_id, "reports/deliberation_playbook_registry.json"],
                    internal_sources=[playbook.playbook_id, "reports/deliberation_playbook_registry.json"],
                )
            )
        for skill in knowledge["skills"]:
            targets.append(
                RealityTarget(
                    target_id=skill.skill_id,
                    target_type="skill",
                    statement=f"Skill {skill.name} remains useful across its task types",
                    confidence=max(skill.success_rate, skill.average_score / 100.0),
                    trust_score=max(skill.success_rate, 0.5),
                    verification_success=1.0 if skill.sample_count else 0.4,
                    historical_quality=skill.average_score / 100.0,
                    outcome_quality=max(0.0, min(1.0, skill.average_roi or skill.success_rate)),
                    sources=[skill.skill_id, "reports/deliberation_skill_registry.json"],
                    internal_sources=[skill.skill_id, "reports/deliberation_skill_registry.json"],
                )
            )
        return targets

    def align(self, observations: dict[str, list[RealityObservation]] | None = None) -> dict[str, Any]:
        observations = observations or {}
        targets = self.build_targets()
        scores = {target.target_id: compute_reality_score(target, observations.get(target.target_id, [])) for target in targets}
        diversity = measure_knowledge_diversity(targets)
        challenges = RealityChallengeEngine().challenge(targets, observations)
        registry = self.belief_registry.seed_from_targets(targets, scores)
        evolved = evolve_beliefs(registry, challenges)
        self.belief_registry.save(evolved)
        fitness = [FitnessEngine().score(target).to_dict() for target in targets]
        avg_confidence = sum(target.confidence for target in targets) / max(1, len(targets))
        avg_trust = sum(target.trust_score for target in targets) / max(1, len(targets))
        self_reference = diversity["internal_ratio"]
        echo = detect_echo_chamber(
            confidence=avg_confidence,
            trust=avg_trust,
            diversity_score=diversity["diversity_score"],
            self_reference=self_reference,
        )
        reality_score = sum(item["reality_score"] for item in scores.values()) / max(1, len(scores))
        return {
            "targets": [target.to_dict() for target in targets],
            "scores": scores,
            "reality_score": round(reality_score, 2),
            "diversity": diversity,
            "challenges": [item.to_dict() for item in challenges],
            "beliefs": {key: value.to_dict() for key, value in evolved.items()},
            "fitness": fitness,
            "echo": echo,
            "governance": {
                "advisory_only": True,
                "may_override_guardian": False,
                "may_modify_provider_permissions": False,
                "may_execute_actions": False,
            },
        }
