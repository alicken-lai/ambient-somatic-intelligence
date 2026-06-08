"""
Anomaly decay — time-based attenuation of an anomaly's salience.

An anomaly that was salient a while ago should matter less now unless it
recurs.  ``apply`` returns the value decayed by an exponential half-life based
on how long ago the anomaly was observed.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


class AnomalyDecay:
    """Exponentially decays an anomaly value by its age."""

    def __init__(self, half_life_seconds: float = 300.0) -> None:
        self.half_life_seconds = max(1e-6, float(half_life_seconds))

    def apply(self, value: float, observed_at: datetime) -> float:
        """Return *value* decayed by the age of *observed_at*."""
        now = datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age = max(0.0, (now - observed_at).total_seconds())
        factor = math.exp(-math.log(2) * age / self.half_life_seconds)
        return max(0.0, min(1.0, float(value) * factor))
