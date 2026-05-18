"""L2 Instinct Memory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer


@dataclass
class InstinctEntry:
    entry_id: str
    timestamp: datetime
    source_episodes: list[str]
    observation: str
    trigger_conditions: list[str]
    confidence: float
    contextual_applicability: list[str] = field(default_factory=list)
    occurrence_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_validated: datetime | None = None
    contradiction_count: int = 0
    layer: MemoryLayer = MemoryLayer.L2_INSTINCT

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "source_episodes": list(self.source_episodes),
            "observation": self.observation,
            "trigger_conditions": list(self.trigger_conditions),
            "confidence": self.confidence,
            "contextual_applicability": list(self.contextual_applicability),
            "occurrence_count": self.occurrence_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_validated": (
                self.last_validated.isoformat() if self.last_validated else None
            ),
            "contradiction_count": self.contradiction_count,
            "layer": self.layer.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InstinctEntry:
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_episodes=data["source_episodes"],
            observation=data["observation"],
            trigger_conditions=data["trigger_conditions"],
            confidence=data["confidence"],
            contextual_applicability=data.get("contextual_applicability", []),
            occurrence_count=data.get("occurrence_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            last_validated=(
                datetime.fromisoformat(data["last_validated"])
                if data.get("last_validated")
                else None
            ),
            contradiction_count=data.get("contradiction_count", 0),
            layer=MemoryLayer(data.get("layer", MemoryLayer.L2_INSTINCT)),
        )

    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def is_promotion_candidate(self, threshold: float) -> bool:
        return self.confidence >= threshold

    def apply_contradiction(self) -> None:
        self.contradiction_count += 1
