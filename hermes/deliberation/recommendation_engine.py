"""Evidence-based deliberation recommendation engine."""

from __future__ import annotations

from typing import Any

from hermes.deliberation.playbooks import PlaybookSelector
from hermes.deliberation.strategy_engine import DeliberationStrategyEngine


class DeliberationRecommendationEngine:
    def __init__(
        self,
        playbook_selector: PlaybookSelector | None = None,
        strategy_engine: DeliberationStrategyEngine | None = None,
    ):
        self.playbook_selector = playbook_selector or PlaybookSelector()
        self.strategy_engine = strategy_engine or DeliberationStrategyEngine()

    def recommend(self, *, task: str, task_class: str, historical: Any = None) -> dict[str, Any]:
        playbook = self.playbook_selector.select(task=task, task_class=task_class)
        strategy = self.strategy_engine.plan(task=task, task_class=task_class, historical=historical)
        return {
            "best_known_strategy": strategy["strategy"],
            "selected_playbook": playbook.get("selected_playbook"),
            "confidence": min(float(playbook.get("confidence", 0.0)), float(strategy["routing_decision"]["confidence"])),
            "reason": f"{playbook.get('reason')} Strategy reason: {strategy['reason']}",
            "strategy": strategy,
            "playbook": playbook,
            "advisory_only": True,
        }
