"""Playbook models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Playbook:
    playbook_id: str
    name: str
    task_types: list[str]
    recommended_children: list[str]
    verification_depth: str
    guardian_requirements: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    failure_indicators: list[str] = field(default_factory=list)
    success_rate: float = 0.0
    average_roi: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "name": self.name,
            "task_types": self.task_types,
            "recommended_children": self.recommended_children,
            "verification_depth": self.verification_depth,
            "guardian_requirements": self.guardian_requirements,
            "success_criteria": self.success_criteria,
            "failure_indicators": self.failure_indicators,
            "success_rate": self.success_rate,
            "average_roi": self.average_roi,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Playbook":
        return cls(
            playbook_id=str(raw["playbook_id"]),
            name=str(raw["name"]),
            task_types=list(raw.get("task_types", [])),
            recommended_children=list(raw.get("recommended_children", [])),
            verification_depth=str(raw.get("verification_depth", "standard")),
            guardian_requirements=list(raw.get("guardian_requirements", [])),
            success_criteria=list(raw.get("success_criteria", [])),
            failure_indicators=list(raw.get("failure_indicators", [])),
            success_rate=float(raw.get("success_rate", 0.0)),
            average_roi=float(raw.get("average_roi", 0.0)),
        )
