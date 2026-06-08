"""
Uncertainty explainer — explains a forecast uncertainty band in plain terms.

Turns an :class:`UncertaintyBand` into a transparent, probabilistic
interpretation so a forecast band is never presented as a precise value.
"""

from __future__ import annotations

from typing import Any

from attention.forecasting.forecast_uncertainty import UncertaintyBand


class UncertaintyExplainer:
    """Explains forecast uncertainty bands."""

    def explain_band(self, band: UncertaintyBand) -> dict[str, Any]:
        width = band.width()
        interpretation = (
            f"Probabilistic band: most likely around {band.mid:.2f}, plausibly between "
            f"{band.low:.2f} and {band.high:.2f} (width {width:.2f}, confidence "
            f"{band.confidence:.2f}). This is a probabilistic range, not a precise value."
        )
        return {
            "low": round(band.low, 4),
            "mid": round(band.mid, 4),
            "high": round(band.high, 4),
            "confidence": round(band.confidence, 4),
            "width": round(width, 4),
            "interpretation": interpretation,
            "opaque": False,
        }
