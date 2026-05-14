"""L1 Episodic Memory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer


@dataclass
class EpisodicEntry:
    entry_id: str
    timestamp: datetime
    source: str
    content: str
    tags: list[str]
    signal_types: list[str]
    environmental_context: dict[str, Any]
    confidence: float
    access_count: int = 0
    last_accessed: datetime | None = None
    linked_entries: list[str] = field(default_factory=list)
    layer: MemoryLayer = MemoryLayer.L1_EPISODIC

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "content": self.content,
            "tags": list(self.tags),
            "signal_types": list(self.signal_types),
            "environmental_context": dict(self.environmental_context),
            "confidence": self.confidence,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "linked_entries": list(self.linked_entries),
            "layer": self.layer.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EpisodicEntry:
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            content=data["content"],
            tags=data["tags"],
            signal_types=data["signal_types"],
            environmental_context=data["environmental_context"],
            confidence=data["confidence"],
            access_count=data.get("access_count", 0),
            last_accessed=(
                datetime.fromisoformat(data["last_accessed"])
                if data.get("last_accessed")
                else None
            ),
            linked_entries=data.get("linked_entries", []),
            layer=MemoryLayer(data.get("layer", MemoryLayer.L1_EPISODIC)),
        )

    def age_days(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return (now - self.timestamp).total_seconds() / 86400.0

    def is_promotion_candidate(self, threshold: float) -> bool:
        return self.confidence >= threshold
