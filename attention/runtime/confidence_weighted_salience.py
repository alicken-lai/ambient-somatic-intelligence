"""
Confidence-weighted salience — scales salience by calibrated confidence.

Multiplies a salience value by a confidence in ``[0, cap]``.  Because confidence
is always strictly below ``1.0``, weighting can only ever attenuate salience,
never amplify it — preventing confidence-driven runaway escalation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.confidence_cap import apply_confidence_cap


@dataclass
class WeightedSalience:
    """Salience after confidence weighting (never amplified)."""

    salience: float
    confidence: float
    weighted: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "salience": round(self.salience, 4),
            "confidence": round(self.confidence, 4),
            "weighted": round(self.weighted, 4),
        }


class ConfidenceWeightedSalience:
    """Attenuates salience by capped confidence; never amplifies."""

    def weight(self, salience: float, confidence: float) -> WeightedSalience:
        capped = apply_confidence_cap(confidence)
        weighted = max(0.0, float(salience)) * capped
        return WeightedSalience(
            salience=float(salience),
            confidence=capped,
            weighted=weighted,
        )
