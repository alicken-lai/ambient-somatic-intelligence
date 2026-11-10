"""Skill evolution, promotion, and retirement decisions."""

from __future__ import annotations

from typing import Any

from hermes.deliberation.skills import DeliberationSkill


def evaluate_skill_evolution(skills: list[DeliberationSkill]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for skill in skills:
        if skill.sample_count >= 3 and skill.average_roi >= 5 and skill.success_rate >= 0.5:
            status = "promoted"
            reason = "consistent ROI improvement"
        elif skill.sample_count >= 3 and skill.average_roi <= 0 and skill.success_rate <= 0.25:
            status = "retired"
            reason = "weak success and ROI trend"
        else:
            status = "observed"
            reason = "insufficient confidence for promotion or retirement"
        decisions.append({"skill": skill.name, "skill_id": skill.skill_id, "status": status, "reason": reason})
    return decisions
