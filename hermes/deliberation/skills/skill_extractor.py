"""Extract reusable skills from completed deliberation evidence."""

from __future__ import annotations

from statistics import mean
from typing import Any

from hermes.deliberation.skills.skill_models import DeliberationSkill


DEFAULT_STEPS = {
    "architecture": ["SystemArchitect", "RiskAnalyst", "SecurityReviewer", "Verification", "Synthesis"],
    "provider_policy": ["GovernanceReviewer", "PolicyReviewer", "RiskAnalyst", "Verification", "Synthesis"],
    "credential_sensitive": ["SecurityReviewer", "GuardianAdvisor", "VerificationSpecialist", "Verification", "Synthesis"],
    "implementation_review": ["ImplementationEngineer", "TestEngineer", "SecurityReviewer", "Verification", "Synthesis"],
    "research_analysis": ["ResearchAnalyst", "VerificationSpecialist", "CostController", "Verification", "Synthesis"],
}


class SkillExtractor:
    def extract_from_ab_results(self, results: list[dict[str, Any]]) -> list[DeliberationSkill]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for result in results:
            grouped.setdefault(str(result.get("category", "unknown")), []).append(result)
        skills: list[DeliberationSkill] = []
        for task_type, items in grouped.items():
            best_scores = [max(float(card["overall_score"]) for card in item["scorecards"].values()) for item in items]
            wins = [item for item in items if item.get("winner") in {"light", "full"}]
            success_rate = len(wins) / len(items) if items else 0.0
            roi_values = [
                max(float(item["scorecards"]["light"]["overall_score"]), float(item["scorecards"]["full"]["overall_score"]))
                - float(item["scorecards"]["single"]["overall_score"])
                for item in items
            ]
            if not items:
                continue
            skills.append(
                DeliberationSkill(
                    skill_id=f"{task_type}_deliberation",
                    name=f"{task_type.replace('_', ' ').title()} Deliberation Skill",
                    task_types=[task_type],
                    steps=DEFAULT_STEPS.get(task_type, ["Triage", "RiskAnalyst", "Verification", "Synthesis"]),
                    success_rate=round(success_rate, 4),
                    sample_count=len(items),
                    average_score=round(mean(best_scores), 2),
                    average_roi=round(mean(roi_values), 2),
                )
            )
        return skills
