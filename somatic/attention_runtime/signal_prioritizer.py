"""
Signal Prioritizer — Priority queue for somatic signal processing.

Ranks signals by a composite priority score derived from:
  - Signal severity / urgency
  - Current attention weights for the signal type
  - Signal recency
  - Source reliability
  - Governance relevance

Supports manual priority overrides for governance use cases.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from somatic.signal_bus import SomaticSignal, SignalType, SignalUrgency

logger = logging.getLogger(__name__)


@dataclass
class PrioritizedSignal:
    """A signal annotated with its computed priority score."""
    signal: SomaticSignal
    priority_score: float
    factors: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.signal.type.value,
            "urgency": self.signal.urgency.value,
            "source": self.signal.source,
            "message": self.signal.message,
            "priority_score": round(self.priority_score, 4),
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "timestamp": datetime.fromtimestamp(
                self.signal.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class SignalPrioritizer:
    """
    Prioritizes somatic signals for processing order.

    Usage:
        prioritizer = SignalPrioritizer()
        prioritized = prioritizer.prioritize(signals)
        for p in prioritized:
            print(f"{p.signal.type.value}: priority={p.priority_score:.2f}")
    """

    WEIGHT_SEVERITY = 0.30
    WEIGHT_ATTENTION = 0.25
    WEIGHT_RECENCY = 0.20
    WEIGHT_RELIABILITY = 0.10
    WEIGHT_GOVERNANCE = 0.15

    KNOWN_RELIABLE_SOURCES = {
        "cpu", "memory", "disk", "load", "environment",
        "correlator", "rate_tracker",
    }

    def __init__(self):
        self._attention_weights: dict[str, float] = {}
        self._priority_overrides: dict[str, float] = {}
        self._priority_queue: list[PrioritizedSignal] = []
        self._max_queue = 200
        self._governance_sensitive_types: set[str] = {
            SignalType.PAIN.value,
            SignalType.REFLEX.value,
        }

    def set_attention_weights(self, weights: dict[str, float]) -> None:
        """Update attention weights used in priority scoring."""
        self._attention_weights = dict(weights)

    def set_priority_override(self, signal_type: str, priority: float) -> None:
        """Set a manual priority override for a signal type (governance use)."""
        self._priority_overrides[signal_type] = max(0.0, min(1.0, priority))
        logger.info(
            "Priority override set: %s = %.2f", signal_type, priority,
        )

    def clear_priority_override(self, signal_type: str) -> None:
        """Remove a manual priority override."""
        self._priority_overrides.pop(signal_type, None)

    def prioritize(self, signals: list[SomaticSignal]) -> list[PrioritizedSignal]:
        """
        Sort and score signals by composite priority.

        Returns a list sorted by descending priority score.
        """
        prioritized: list[PrioritizedSignal] = []

        for signal in signals:
            override = self._priority_overrides.get(signal.type.value)
            if override is not None:
                prioritized.append(PrioritizedSignal(
                    signal=signal,
                    priority_score=override,
                    factors={"override": override},
                ))
                continue

            severity = self._score_severity(signal)
            attention = self._score_attention(signal)
            recency = self._score_recency(signal)
            reliability = self._score_reliability(signal)
            governance = self._score_governance(signal)

            factors = {
                "severity": severity,
                "attention": attention,
                "recency": recency,
                "reliability": reliability,
                "governance": governance,
            }

            score = (
                self.WEIGHT_SEVERITY * severity
                + self.WEIGHT_ATTENTION * attention
                + self.WEIGHT_RECENCY * recency
                + self.WEIGHT_RELIABILITY * reliability
                + self.WEIGHT_GOVERNANCE * governance
            )

            prioritized.append(PrioritizedSignal(
                signal=signal,
                priority_score=score,
                factors=factors,
            ))

        prioritized.sort(key=lambda p: p.priority_score, reverse=True)

        self._priority_queue = prioritized[:self._max_queue]

        return prioritized

    def get_priority_queue(self) -> list[dict[str, Any]]:
        """Get the current priority queue state."""
        return [p.to_dict() for p in self._priority_queue]

    def _score_severity(self, signal: SomaticSignal) -> float:
        """Score based on signal urgency level."""
        return min(signal.urgency.value / 5.0, 1.0)

    def _score_attention(self, signal: SomaticSignal) -> float:
        """Score based on current attention weight for this signal type."""
        return self._attention_weights.get(signal.type.value, 0.15)

    def _score_recency(self, signal: SomaticSignal) -> float:
        """Score based on how recent the signal is (exponential decay)."""
        age = time.time() - signal.timestamp
        if age < 5.0:
            return 1.0
        elif age < 30.0:
            return 0.8
        elif age < 120.0:
            return 0.5
        elif age < 300.0:
            return 0.3
        return 0.1

    def _score_reliability(self, signal: SomaticSignal) -> float:
        """Score based on source reliability."""
        base_source = signal.source.split(".")[0]
        if base_source in self.KNOWN_RELIABLE_SOURCES:
            return 0.9
        return 0.5

    def _score_governance(self, signal: SomaticSignal) -> float:
        """Score governance relevance."""
        if signal.type.value in self._governance_sensitive_types:
            return 0.8
        if signal.is_critical:
            return 0.7
        return 0.2
