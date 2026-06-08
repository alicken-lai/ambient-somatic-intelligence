"""
Salience pressure forecast — projects attention pressure forward.

Reads the kernel's current load (queue + focus) and projects pressure a step
ahead, reporting headroom (``1 - projected``) and a bounded uncertainty band.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.forecast_uncertainty import ForecastUncertainty, UncertaintyBand
from attention.kernel.attention_kernel import AttentionKernel


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class PressureForecast:
    """A projection of attention pressure for a target."""

    target_id: str
    current_pressure: float
    projected_pressure: float
    headroom: float
    band: UncertaintyBand

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "current_pressure": round(self.current_pressure, 4),
            "projected_pressure": round(self.projected_pressure, 4),
            "headroom": round(self.headroom, 4),
            "band": self.band.to_dict(),
        }


class SaliencePressureForecast:
    """Projects kernel attention pressure forward in time."""

    def __init__(
        self,
        kernel: AttentionKernel,
        uncertainty: ForecastUncertainty | None = None,
        growth_per_step: float = 0.05,
    ) -> None:
        self.kernel = kernel
        self.uncertainty = uncertainty or ForecastUncertainty()
        self.growth_per_step = float(growth_per_step)

    def _current_pressure(self) -> float:
        max_queue = max(1, self.kernel.max_queue)
        max_focus = max(1, self.kernel.allocator.max_slots)
        queue_load = _clamp_unit(self.kernel.state.queue_depth / max_queue)
        focus_load = _clamp_unit(self.kernel.state.focused_count / max_focus)
        return _clamp_unit(0.6 * queue_load + 0.4 * focus_load)

    def forecast(self, target_id: str, horizon_factor: float = 1.0) -> PressureForecast:
        current = self._current_pressure()
        projected = _clamp_unit(current + self.growth_per_step * max(0.0, horizon_factor))
        headroom = _clamp_unit(1.0 - projected)
        band = self.uncertainty.band(projected, horizon_factor=horizon_factor, sample_count=1)
        return PressureForecast(
            target_id=target_id,
            current_pressure=current,
            projected_pressure=projected,
            headroom=headroom,
            band=band,
        )
