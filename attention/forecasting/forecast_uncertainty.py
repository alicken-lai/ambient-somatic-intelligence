"""
Forecast uncertainty — bounded probabilistic bands around projected values.

Every forecast value carries an :class:`UncertaintyBand` (low / mid / high with a
confidence).  Uncertainty widens with the forecast horizon and narrows with more
samples, but the spread is always capped (``max_spread``) so the system never
claims a precise prediction — forecasts are *projections, not predictions*.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class UncertaintyBand:
    """A probabilistic band: ``low <= mid <= high`` with a confidence."""

    low: float
    mid: float
    high: float
    confidence: float = 0.5

    def width(self) -> float:
        return self.high - self.low

    def to_dict(self) -> dict[str, Any]:
        return {
            "low": round(self.low, 4),
            "mid": round(self.mid, 4),
            "high": round(self.high, 4),
            "confidence": round(self.confidence, 4),
            "width": round(self.width(), 4),
        }


class ForecastUncertainty:
    """Produces bounded uncertainty bands for forecast values."""

    def __init__(self, max_spread: float = 0.35, base_spread: float = 0.08) -> None:
        self.max_spread = max(0.0, min(1.0, float(max_spread)))
        self.base_spread = max(0.0, float(base_spread))

    def spread_for(self, horizon_factor: float = 1.0, sample_count: int = 1) -> float:
        raw = self.base_spread * (1.0 + 0.3 * max(0.0, horizon_factor))
        raw /= math.sqrt(max(1, int(sample_count)) + 1)
        return min(self.max_spread, raw)

    def band(
        self,
        value: float,
        horizon_factor: float = 1.0,
        sample_count: int = 1,
    ) -> UncertaintyBand:
        mid = _clamp_unit(value)
        spread = self.spread_for(horizon_factor, sample_count)
        half = spread / 2.0
        low = _clamp_unit(mid - half)
        high = _clamp_unit(mid + half)
        confidence = _clamp_unit(1.0 - spread)
        return UncertaintyBand(low=low, mid=mid, high=high, confidence=confidence)
