"""Select reusable playbooks using evidence."""

from __future__ import annotations

from typing import Any

from hermes.deliberation.playbooks.playbook_models import Playbook
from hermes.deliberation.playbooks.playbook_registry import PlaybookRegistry


class PlaybookSelector:
    def __init__(self, registry: PlaybookRegistry | None = None):
        self.registry = registry or PlaybookRegistry()

    def select(self, *, task: str, task_class: str, historical_success: dict[str, float] | None = None) -> dict[str, Any]:
        playbooks = self.registry.load()
        candidates = [playbook for playbook in playbooks.values() if task_class in playbook.task_types]
        if not candidates:
            return {"selected_playbook": None, "confidence": 0.0, "reason": "No playbook matched task class."}
        historical_success = historical_success or {}
        selected = max(candidates, key=lambda item: historical_success.get(item.playbook_id, item.success_rate + item.average_roi / 100.0))
        score = historical_success.get(selected.playbook_id, selected.success_rate + selected.average_roi / 100.0)
        confidence = min(0.95, max(0.45, score))
        return {
            "selected_playbook": selected.playbook_id,
            "confidence": round(confidence, 3),
            "reason": f"{selected.name} matches {task_class} and has the best available success evidence.",
            "playbook": selected.to_dict(),
        }
