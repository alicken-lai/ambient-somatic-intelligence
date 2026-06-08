"""
Forecast explainer — narrates a unified attention forecast result.

Produces a human-readable, explicitly-probabilistic summary of an
:class:`AttentionForecastResult`, carrying through the result's
projection-not-prediction disclaimer.
"""

from __future__ import annotations

from typing import Any

from attention.forecasting.attention_forecast import AttentionForecastResult


class ForecastExplainer:
    """Explains a unified attention forecast result."""

    def explain(self, result: AttentionForecastResult) -> dict[str, Any]:
        direction = result.trajectory.direction if result.trajectory else "stable"
        headroom = result.pressure.headroom if result.pressure else 1.0
        summary = (
            f"Probabilistic attention forecast over {result.window}: "
            f"{len(result.projections)} projected steps, trajectory '{direction}', "
            f"pressure headroom {headroom:.2f}. This is a projection, not a prediction."
        )
        return {
            "summary": summary,
            "window": result.window,
            "projection_count": len(result.projections),
            "trajectory_direction": direction,
            "pressure_headroom": round(headroom, 4),
            "disclaimer": result.disclaimer,
            "opaque": False,
        }
