"""Deliberation strategy engine."""

from __future__ import annotations

from typing import Any

from hermes.deliberation.child_selector import ChildSelector
from hermes.deliberation.memory import EffectivenessRecord
from hermes.deliberation.router import RoutingDecision, RoutingIntelligenceEngine


class DeliberationStrategyEngine:
    def __init__(
        self,
        routing_engine: RoutingIntelligenceEngine | None = None,
        child_selector: ChildSelector | None = None,
    ):
        self.routing_engine = routing_engine or RoutingIntelligenceEngine()
        self.child_selector = child_selector or ChildSelector()

    def plan(
        self,
        *,
        task: str,
        task_class: str,
        historical: EffectivenessRecord | None = None,
        risk_level: str = "normal",
    ) -> dict[str, Any]:
        decision = self.routing_engine.recommend(
            task=task,
            task_class=task_class,
            historical=historical,
            risk_level=risk_level,
        )
        max_children = _children_for_mode(decision.recommended_mode)
        selected = self.child_selector.select(task_class, max_children=max_children, risk_level=risk_level)
        verification_depth = "deep" if decision.recommended_mode in {"full", "guardian_required"} else "standard"
        expected_roi = historical.avg_roi if historical else 0.0
        return {
            "strategy": _strategy_name(decision),
            "selected_children": [role.to_dict() for role in selected],
            "expected_roi": expected_roi,
            "verification_depth": verification_depth,
            "guardian_involvement": decision.recommended_mode == "guardian_required",
            "routing_decision": decision.to_dict(),
            "reason": decision.reason,
        }


def _children_for_mode(mode: str) -> int:
    if mode == "single":
        return 0
    if mode == "light":
        return 2
    return 3


def _strategy_name(decision: RoutingDecision) -> str:
    return f"{decision.recommended_mode}_adaptive_strategy"
