"""
Forecast humility — attenuates confidence in proportion to uncertainty.

Epistemic humility: the wider the uncertainty band and the higher the raw
confidence, the more the confidence is pulled back.  The humility factor is
always in ``[0, 1]`` so it can only ever reduce, never amplify, confidence.
"""

from __future__ import annotations


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class ForecastHumility:
    """Reduces confidence as a function of uncertainty and overconfidence."""

    def __init__(
        self,
        band_weight: float = 0.5,
        overconfidence_weight: float = 0.5,
        high_confidence_threshold: float = 0.8,
    ) -> None:
        self.band_weight = float(band_weight)
        self.overconfidence_weight = float(overconfidence_weight)
        self.high_confidence_threshold = float(high_confidence_threshold)

    def humility_factor(self, confidence: float, band_width: float = 0.15) -> float:
        """A multiplier in ``[0, 1]`` that never amplifies confidence."""
        conf = _clamp_unit(confidence)
        bw = max(0.0, float(band_width))
        overconfidence = max(0.0, conf - self.high_confidence_threshold)
        factor = 1.0 - bw * self.band_weight - overconfidence * self.overconfidence_weight
        return _clamp_unit(factor)

    def humble_confidence(self, confidence: float, band_width: float = 0.15) -> float:
        """Apply the humility factor to *confidence*."""
        return _clamp_unit(confidence) * self.humility_factor(confidence, band_width=band_width)
