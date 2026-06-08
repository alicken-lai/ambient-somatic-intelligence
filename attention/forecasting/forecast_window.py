"""
Forecast windows — the bounded horizons the attention layer projects over.

Forecasts are produced for a fixed set of windows (6h / 24h / 7d / 30d).  No
window may exceed :data:`MAX_HORIZON_SECONDS`; the system deliberately refuses to
project further than 30 days, reflecting the "projection, not prediction"
discipline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Hard ceiling on any forecast horizon: 30 days.
MAX_HORIZON_SECONDS: int = 2_592_000


@dataclass(frozen=True)
class ForecastWindow:
    """A single forecast horizon with a discrete number of projection steps."""

    name: str
    horizon_seconds: int
    steps: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "horizon_seconds": self.horizon_seconds,
            "steps": self.steps,
        }


FORECAST_WINDOWS: dict[str, ForecastWindow] = {
    "6h": ForecastWindow("6h", 21_600, 6),
    "24h": ForecastWindow("24h", 86_400, 8),
    "7d": ForecastWindow("7d", 604_800, 7),
    "30d": ForecastWindow("30d", MAX_HORIZON_SECONDS, 6),
}
