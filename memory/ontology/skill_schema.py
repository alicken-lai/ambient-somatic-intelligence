"""L3 Skill Memory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer


@dataclass
class SkillMemoryEntry:
    entry_id: str
    timestamp: datetime
    source_instincts: list[str]
    skill_name: str
    description: str
    workflow_steps: list[str]
    confidence: float
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: float = 0.0
    contexts_validated: list[str] = field(default_factory=list)
    linked_skill_id: str | None = None
    last_executed: datetime | None = None
    layer: MemoryLayer = MemoryLayer.L3_SKILL

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "source_instincts": list(self.source_instincts),
            "skill_name": self.skill_name,
            "description": self.description,
            "workflow_steps": list(self.workflow_steps),
            "confidence": self.confidence,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_duration_ms": self.avg_duration_ms,
            "contexts_validated": list(self.contexts_validated),
            "linked_skill_id": self.linked_skill_id,
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
            "layer": self.layer.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillMemoryEntry:
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_instincts=data["source_instincts"],
            skill_name=data["skill_name"],
            description=data["description"],
            workflow_steps=data["workflow_steps"],
            confidence=data["confidence"],
            execution_count=data.get("execution_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            avg_duration_ms=data.get("avg_duration_ms", 0.0),
            contexts_validated=data.get("contexts_validated", []),
            linked_skill_id=data.get("linked_skill_id"),
            last_executed=(
                datetime.fromisoformat(data["last_executed"])
                if data.get("last_executed")
                else None
            ),
            layer=MemoryLayer(data.get("layer", MemoryLayer.L3_SKILL)),
        )

    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def is_promotion_candidate(self, threshold: float) -> bool:
        return self.confidence >= threshold

    def cross_context_count(self) -> int:
        return len(self.contexts_validated)
