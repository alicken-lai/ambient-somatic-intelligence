"""
Precursor signal — an early, weak indicator that may precede a salient event.

A :class:`PrecursorSignal` represents a recognised pattern (``pattern_id``) with
an associated ``strength`` and originating ``domain``.  The consolidation and
forecasting layers accumulate precursor signals to reinforce or forecast the
emergence of higher-salience targets.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PrecursorSignal:
    """A weak, early indicator keyed by a recognised pattern."""

    pattern_id: str
    strength: float
    domain: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def __post_init__(self) -> None:
        self.strength = max(0.0, min(1.0, float(self.strength)))
        if self.metadata is None:
            self.metadata = {}

    @property
    def age_seconds(self) -> float:
        """Seconds elapsed since the precursor was observed."""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "signal_id": self.signal_id,
            "pattern_id": self.pattern_id,
            "strength": round(self.strength, 4),
            "domain": self.domain,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrecursorSignal":
        """Reconstruct from a serialised dict."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now(timezone.utc)
        return cls(
            pattern_id=data["pattern_id"],
            strength=float(data["strength"]),
            domain=data.get("domain", "unknown"),
            metadata=dict(data.get("metadata", {})),
            signal_id=data.get("signal_id", uuid.uuid4().hex),
            timestamp=ts,
        )
