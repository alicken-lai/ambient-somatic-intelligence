"""Dynamic child selection for Mother deliberation."""

from __future__ import annotations

from hermes.deliberation.child_registry import ChildRole, get_role_registry
from hermes.deliberation.selection_policies import SELECTION_POLICIES


class ChildSelector:
    def __init__(self, registry: dict[str, ChildRole] | None = None):
        self.registry = registry or get_role_registry()

    def select(self, task_class: str, *, max_children: int = 3, risk_level: str = "normal") -> list[ChildRole]:
        role_names = list(SELECTION_POLICIES.get(task_class, ["SystemArchitect", "RiskAnalyst"]))
        if risk_level == "high" and "GuardianAdvisor" not in role_names:
            role_names.insert(0, "GuardianAdvisor")
        selected: list[ChildRole] = []
        for name in role_names:
            role = self.registry.get(name)
            if role and role.name not in {item.name for item in selected}:
                selected.append(role)
            if len(selected) >= max_children:
                break
        return selected
