"""
Noise classifier — flags repetitive, low-salience signals as background noise.

A signal that recurs many times while staying below a salience ceiling is
treated as noise (e.g. a steady heartbeat).  The classifier tracks per-pattern
occurrence counts and classifies once a signal has repeated past a threshold.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class NoiseClassification:
    """Outcome of classifying a single observation."""

    is_noise: bool
    count: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"is_noise": self.is_noise, "count": self.count, "reason": self.reason}


class NoiseClassifier:
    """Classifies repetitive low-salience signals as noise."""

    def __init__(self, repeat_threshold: int = 3, value_ceiling: float = 0.2) -> None:
        self.repeat_threshold = max(1, int(repeat_threshold))
        self.value_ceiling = float(value_ceiling)
        self._counts: dict[tuple[str, str], int] = defaultdict(int)

    def observe(self, domain: str, signal_type: str, value: float) -> NoiseClassification:
        """Record an observation and classify it as noise or signal."""
        key = (domain, signal_type)
        self._counts[key] += 1
        count = self._counts[key]

        if value > self.value_ceiling:
            return NoiseClassification(False, count, "above_salience_ceiling")
        if count >= self.repeat_threshold:
            return NoiseClassification(True, count, "repetitive_low_salience")
        return NoiseClassification(False, count, "below_repeat_threshold")
