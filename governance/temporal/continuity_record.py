"""Continuity record — bounded snapshot of epoch-local civilization memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from observability.v04.metric_normalizer import clamp01


@dataclass
class ContinuityRecord:
    """Single bounded continuity snapshot — never claims immortal persistence."""

    record_id: str
    epoch_id: str
    runtime_id: str
    summary: str
    confidence: float = 0.7
    replay_hint: float = 0.0
    retention_hours: float = 168.0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        epoch_id: str,
        runtime_id: str,
        summary: str,
        confidence: float = 0.7,
        replay_hint: float = 0.0,
        retention_hours: float = 168.0,
        metadata: dict[str, Any] | None = None,
    ) -> ContinuityRecord:
        return cls(
            record_id=str(uuid4()),
            epoch_id=epoch_id,
            runtime_id=runtime_id,
            summary=summary,
            confidence=clamp01(confidence),
            replay_hint=clamp01(replay_hint),
            retention_hours=max(1.0, retention_hours),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "epoch_id": self.epoch_id,
            "runtime_id": self.runtime_id,
            "summary": self.summary,
            "confidence": round(self.confidence, 4),
            "replay_hint": round(self.replay_hint, 4),
            "retention_hours": round(self.retention_hours, 2),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "advisory_only": True,
        }
