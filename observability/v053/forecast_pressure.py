"""Forecast pressure observability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.forecasting.salience_pressure_forecast import PressureForecast, SaliencePressureForecast


@dataclass
class ForecastPressureMetrics:
    current: float = 0.0
    projected: float = 0.0
    headroom: float = 1.0
    band_width: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": round(self.current, 4),
            "projected": round(self.projected, 4),
            "headroom": round(self.headroom, 4),
            "band_width": round(self.band_width, 4),
        }


def collect_forecast_pressure_metrics(
    forecaster: SaliencePressureForecast,
    target_id: str,
) -> ForecastPressureMetrics:
    pf: PressureForecast = forecaster.forecast(target_id)
    return ForecastPressureMetrics(
        current=pf.current_pressure,
        projected=pf.projected_pressure,
        headroom=pf.headroom,
        band_width=pf.band.width(),
    )
