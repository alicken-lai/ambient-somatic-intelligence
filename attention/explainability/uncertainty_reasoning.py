"""
Uncertainty reasoning — explains why an uncertainty band forbids certainty.

Reasons over a forecast :class:`UncertaintyBand`, reporting its spread and
explicitly affirming that certainty is forbidden (``certainty_forbidden``).
"""

from __future__ import annotations

from typing import Any

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from attention.forecasting.forecast_uncertainty import UncertaintyBand


class UncertaintyReasoning:
    """Reasons over a forecast uncertainty band."""

    def reason_band(self, band: UncertaintyBand) -> dict[str, Any]:
        width = band.width()
        interpretation = (
            f"The value plausibly lies in [{band.low:.2f}, {band.high:.2f}] "
            f"(spread {width:.2f}); confidence {band.confidence:.2f} is bounded and "
            f"certainty is forbidden (ceiling {ABSOLUTE_MAX_CONFIDENCE})."
        )
        return {
            "low": round(band.low, 4),
            "mid": round(band.mid, 4),
            "high": round(band.high, 4),
            "width": round(width, 4),
            "confidence": round(band.confidence, 4),
            "certainty_forbidden": True,
            "interpretation": interpretation,
            "opaque": False,
        }
