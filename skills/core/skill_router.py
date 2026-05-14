"""
Skill Router — Route tasks to the best-matching skill with governance checks.

The router sits between task requests and skill execution:
  - Finds matching skills via the registry
  - Checks governance clearance before routing
  - Supports fallback chains (try skill A, if fails try skill B)
  - Logs all routing decisions for observability
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from skills.core.skill_schema import SkillContext, SkillResult, SkillSchema
from skills.core.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)

GOVERNANCE_ORDER = {
    "ALLOW": 0,
    "REVIEW_REQUIRED": 1,
    "BLOCK_WITHOUT_APPROVAL": 2,
}


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    selected_skill: SkillSchema | None
    confidence: float
    alternatives: list[tuple[str, float]]
    governance_check_required: bool
    routing_reason: str
    routed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_skill": self.selected_skill.name if self.selected_skill else None,
            "selected_skill_id": (
                self.selected_skill.skill_id if self.selected_skill else None
            ),
            "confidence": round(self.confidence, 4),
            "alternatives": [
                {"skill_name": name, "confidence": round(c, 4)}
                for name, c in self.alternatives
            ],
            "governance_check_required": self.governance_check_required,
            "routing_reason": self.routing_reason,
        }


class SkillRouter:
    """
    Routes task descriptions to the most appropriate skill.

    Integrates with the SkillRegistry for discovery and checks governance
    requirements before allowing execution. Supports fallback chains so
    that if the primary skill fails, alternatives are tried automatically.

    Usage:
        router = SkillRouter(registry)
        decision = router.route("explain the current anomaly", context={})
        if decision.selected_skill:
            result = router.execute_with_fallback(decision, context)
    """

    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    def route(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
        governance_clearance: str = "ALLOW",
    ) -> RoutingDecision:
        """
        Find the best skill for a task and produce a routing decision.

        Checks governance level — if the skill requires higher clearance
        than provided, the decision flags governance_check_required.
        """
        context = context or {}
        candidates = self._registry.find_best(task_description, context)

        if not candidates:
            logger.info("No skill matched task: '%s'", task_description[:80])
            return RoutingDecision(
                selected_skill=None,
                confidence=0.0,
                alternatives=[],
                governance_check_required=False,
                routing_reason="No matching skill found",
            )

        best_skill, best_score = candidates[0]
        alternatives = [
            (s.name, score) for s, score in candidates[1:]
        ]

        gov_required = self._needs_governance_review(
            best_skill, governance_clearance,
        )

        reason = (
            f"Matched '{best_skill.name}' v{best_skill.version} "
            f"with confidence {best_score:.3f}"
        )
        if gov_required:
            reason += (
                f" (governance: {best_skill.governance_level} > "
                f"clearance: {governance_clearance})"
            )

        decision = RoutingDecision(
            selected_skill=best_skill,
            confidence=best_score,
            alternatives=alternatives,
            governance_check_required=gov_required,
            routing_reason=reason,
        )

        logger.info(
            "Routed '%s' → skill '%s' (confidence=%.3f, gov_check=%s)",
            task_description[:60], best_skill.name, best_score, gov_required,
        )
        return decision

    def execute_with_fallback(
        self,
        decision: RoutingDecision,
        context: SkillContext,
        max_attempts: int = 3,
    ) -> SkillResult:
        """
        Execute the selected skill; on failure, try alternatives in order.

        Returns the first successful SkillResult, or the last failure
        if all attempts are exhausted.
        """
        if decision.selected_skill is None:
            return SkillResult(
                success=False,
                error="No skill was selected by the router",
                trace_id=context.trace_id,
            )

        if decision.governance_check_required:
            return SkillResult(
                success=False,
                error=(
                    f"Governance clearance insufficient: "
                    f"skill requires {decision.selected_skill.governance_level}"
                ),
                trace_id=context.trace_id,
            )

        chain = [decision.selected_skill]
        for alt_name, _ in decision.alternatives[:max_attempts - 1]:
            alt_skill = self._find_skill_by_name(alt_name)
            if alt_skill:
                chain.append(alt_skill)

        last_result: SkillResult | None = None
        for i, skill in enumerate(chain[:max_attempts]):
            logger.debug(
                "Fallback attempt %d/%d: skill '%s'", i + 1, max_attempts, skill.name,
            )
            result = skill.run(context)
            if result.success:
                return result
            last_result = result
            logger.warning(
                "Skill '%s' failed (attempt %d): %s",
                skill.name, i + 1, result.error,
            )

        return last_result or SkillResult(
            success=False,
            error="All fallback attempts exhausted",
            trace_id=context.trace_id,
        )

    def _needs_governance_review(
        self, skill: SkillSchema, clearance: str,
    ) -> bool:
        """Check if the skill's governance level exceeds the given clearance."""
        skill_level = GOVERNANCE_ORDER.get(skill.governance_level, 1)
        clearance_level = GOVERNANCE_ORDER.get(clearance, 0)
        return skill_level > clearance_level

    def _find_skill_by_name(self, name: str) -> SkillSchema | None:
        """Lookup a skill by name in the registry."""
        for skill in self._registry.list_all():
            if skill.name == name:
                return skill
        return None
