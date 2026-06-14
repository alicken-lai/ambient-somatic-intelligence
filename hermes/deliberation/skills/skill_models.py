"""Skill models for reusable deliberation knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DeliberationSkill:
    skill_id: str
    name: str
    task_types: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    success_rate: float = 0.0
    sample_count: int = 0
    average_score: float = 0.0
    average_roi: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "task_types": self.task_types,
            "steps": self.steps,
            "success_rate": self.success_rate,
            "sample_count": self.sample_count,
            "average_score": self.average_score,
            "average_roi": self.average_roi,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DeliberationSkill":
        return cls(
            skill_id=str(raw["skill_id"]),
            name=str(raw["name"]),
            task_types=list(raw.get("task_types", [])),
            steps=list(raw.get("steps", [])),
            success_rate=float(raw.get("success_rate", 0.0)),
            sample_count=int(raw.get("sample_count", 0)),
            average_score=float(raw.get("average_score", 0.0)),
            average_roi=float(raw.get("average_roi", 0.0)),
        )
