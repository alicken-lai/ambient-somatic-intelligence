"""Bounded cognition record — advisory snapshot of civilization-local agency state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from observability.v04.metric_normalizer import clamp01


@dataclass
class BoundedCognitionRecord:
    record_id: str
    agency_id: str
    runtime_id: str
    summary: str
    confidence: float = 0.7
    selfhood_hint: float = 0.0
    retention_hours: float = 168.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        agency_id: str,
        runtime_id: str,
        summary: str,
        confidence: float = 0.7,
        selfhood_hint: float = 0.0,
        retention_hours: float = 168.0,
        metadata: dict[str, Any] | None = None,
    ) -> BoundedCognitionRecord:
        return cls(
            record_id=str(uuid4()),
            agency_id=agency_id,
            runtime_id=runtime_id,
            summary=summary,
            confidence=clamp01(confidence),
            selfhood_hint=clamp01(selfhood_hint),
            retention_hours=max(1.0, retention_hours),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agency_id": self.agency_id,
            "runtime_id": self.runtime_id,
            "summary": self.summary,
            "confidence": round(self.confidence, 4),
            "selfhood_hint": round(self.selfhood_hint, 4),
            "retention_hours": round(self.retention_hours, 2),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
            "advisory_only": True,
        }
