"""
Unified Telemetry Record Schema.

Every telemetry data point in the Ambient OS — regardless of origin —
is normalized into a TelemetryRecord before storage, replay, or analysis.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DataOrigin(str, Enum):
    REAL = "REAL"
    INTERPOLATED = "INTERPOLATED"
    UNKNOWN = "UNKNOWN"


VALID_CATEGORIES = frozenset({
    "health", "incident", "action", "state", "metric",
    "governance", "somatic", "episodic", "semantic",
    "procedural", "reflex", "checkpoint", "attention",
})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TelemetryRecord:
    """Canonical representation of a single telemetry data point."""

    record_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    source: str = ""
    timestamp: str = ""
    timestamp_unix: float = 0.0
    category: str = "metric"
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    origin: str = "REAL"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.origin not in {e.value for e in DataOrigin}:
            self.origin = DataOrigin.UNKNOWN.value
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source": self.source,
            "timestamp": self.timestamp,
            "timestamp_unix": self.timestamp_unix,
            "category": self.category,
            "payload": self.payload,
            "confidence": round(self.confidence, 6),
            "origin": self.origin,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelemetryRecord:
        return cls(
            record_id=data.get("record_id", uuid.uuid4().hex[:16]),
            source=data.get("source", ""),
            timestamp=data.get("timestamp", ""),
            timestamp_unix=float(data.get("timestamp_unix", 0.0)),
            category=data.get("category", "metric"),
            payload=data.get("payload", {}),
            confidence=float(data.get("confidence", 1.0)),
            origin=data.get("origin", DataOrigin.REAL.value),
            metadata=data.get("metadata", {}),
        )

    @property
    def datetime_utc(self) -> datetime:
        if self.timestamp_unix > 0:
            return datetime.fromtimestamp(self.timestamp_unix, tz=timezone.utc)
        return _utc_now()
