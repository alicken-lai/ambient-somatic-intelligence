"""
Attention State — Unified signal representation and attention state machine.

Provides the core data types for the attention architecture:
  - AttentionSignal: domain-agnostic signal that any subsystem can produce
  - TemporalContext: time-of-day and operational phase awareness
  - AttentionState (renamed to AttentionSnapshot to avoid collision with
    somatic.attention_manager.AttentionState): full attention state with
    budget, temporal context, and history

These types bridge the gap between domain-specific signals (somatic, governance,
memory, task) and the unified attention layer that prioritises across all of them.
"""

from __future__ import annotations

import uuid
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from somatic.attention_manager import AttentionLevel

logger = logging.getLogger(__name__)


class OperationalPhase(str, Enum):
    """High-level operational phase of the system."""
    STARTUP = "startup"
    ACTIVE = "active"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"


class DayPhase(str, Enum):
    """Coarse time-of-day bucket for circadian-aware attention."""
    MORNING = "morning"      # 06:00 – 12:00
    AFTERNOON = "afternoon"  # 12:00 – 18:00
    EVENING = "evening"      # 18:00 – 22:00
    NIGHT = "night"          # 22:00 – 06:00


@dataclass
class AttentionSignal:
    """
    A unified, domain-agnostic attention candidate.

    Any subsystem (somatic, governance, memory, task, external) can produce
    an AttentionSignal.  The attention layer scores and prioritises these
    without needing to know the originating domain's internals.
    """
    source_domain: str
    signal_type: str
    raw_value: float
    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    source_ref: Optional[str] = None

    def __post_init__(self) -> None:
        self.raw_value = max(0.0, min(1.0, self.raw_value))

    @property
    def age_seconds(self) -> float:
        """Seconds elapsed since the signal was created."""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict."""
        return {
            "signal_id": self.signal_id,
            "source_domain": self.source_domain,
            "signal_type": self.signal_type,
            "raw_value": round(self.raw_value, 4),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "source_ref": self.source_ref,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttentionSignal:
        """Reconstruct from a serialised dict."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now(timezone.utc)
        return cls(
            signal_id=data.get("signal_id", uuid.uuid4().hex),
            source_domain=data["source_domain"],
            signal_type=data["signal_type"],
            raw_value=float(data["raw_value"]),
            timestamp=ts,
            metadata=data.get("metadata", {}),
            source_ref=data.get("source_ref"),
        )


def _current_day_phase() -> DayPhase:
    """Determine the current day phase from UTC hour."""
    hour = datetime.now(timezone.utc).hour
    if 6 <= hour < 12:
        return DayPhase.MORNING
    elif 12 <= hour < 18:
        return DayPhase.AFTERNOON
    elif 18 <= hour < 22:
        return DayPhase.EVENING
    return DayPhase.NIGHT


@dataclass
class TemporalContext:
    """Time-of-day and operational-phase awareness for attention decisions."""
    day_phase: DayPhase = field(default_factory=_current_day_phase)
    operational_phase: OperationalPhase = OperationalPhase.ACTIVE
    uptime_seconds: float = 0.0
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_phase": self.day_phase.value,
            "operational_phase": self.operational_phase.value,
            "uptime_seconds": round(self.uptime_seconds, 1),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemporalContext:
        return cls(
            day_phase=DayPhase(data["day_phase"]),
            operational_phase=OperationalPhase(data["operational_phase"]),
            uptime_seconds=float(data.get("uptime_seconds", 0.0)),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc),
        )


@dataclass
class AttentionSnapshot:
    """
    Full attention state at a point in time.

    Named *Snapshot* to avoid collision with the existing
    ``somatic.attention_manager.AttentionState`` which is narrower in scope.
    """
    current_level: AttentionLevel = AttentionLevel.FOCUSED
    active_signals: list[AttentionSignal] = field(default_factory=list)
    salience_scores: dict[str, float] = field(default_factory=dict)
    attention_budget: Any = None  # Typed as Any; set to AttentionBudget at runtime
    temporal_context: TemporalContext = field(default_factory=TemporalContext)
    history: deque = field(default_factory=lambda: deque(maxlen=50))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def record(self) -> None:
        """Push a lightweight snapshot of the current state into history."""
        self.history.append({
            "level": int(self.current_level),
            "active_count": len(self.active_signals),
            "top_salience": max(self.salience_scores.values()) if self.salience_scores else 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self) -> dict[str, Any]:
        """Serialise the full state."""
        return {
            "current_level": self.current_level.name,
            "current_level_value": int(self.current_level),
            "active_signals": [s.to_dict() for s in self.active_signals],
            "salience_scores": {k: round(v, 4) for k, v in self.salience_scores.items()},
            "attention_budget": self.attention_budget.to_dict() if self.attention_budget and hasattr(self.attention_budget, "to_dict") else None,
            "temporal_context": self.temporal_context.to_dict(),
            "history_length": len(self.history),
            "history_recent": list(self.history)[-5:],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttentionSnapshot:
        """Reconstruct from a serialised dict (budget must be re-attached)."""
        signals = [AttentionSignal.from_dict(s) for s in data.get("active_signals", [])]
        tc = TemporalContext.from_dict(data["temporal_context"]) if "temporal_context" in data else TemporalContext()
        history: deque = deque(data.get("history_recent", []), maxlen=50)
        return cls(
            current_level=AttentionLevel[data.get("current_level", "FOCUSED")],
            active_signals=signals,
            salience_scores=data.get("salience_scores", {}),
            temporal_context=tc,
            history=history,
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
        )
