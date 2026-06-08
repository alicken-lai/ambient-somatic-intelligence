"""
Precursor reliability — how much a precursor signal can be trusted.

Scores the reliability of an early :class:`PrecursorSignal` from its strength,
then passes the score through the shared confidence cap so reliability never
reaches certainty (``ABSOLUTE_MAX_CONFIDENCE``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.confidence_cap import apply_confidence_cap
from attention.core.precursor_signal import PrecursorSignal


@dataclass
class ReliabilityScore:
    """A capped reliability score for a precursor signal."""

    pattern_id: str
    reliability: float
    raw: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "reliability": round(self.reliability, 6),
            "raw": round(self.raw, 6),
        }


class PrecursorReliability:
    """Scores precursor signal reliability under the confidence cap."""

    def __init__(self, base: float = 0.2, strength_weight: float = 0.8) -> None:
        self.base = base
        self.strength_weight = strength_weight

    def score(self, signal: PrecursorSignal) -> ReliabilityScore:
        raw = self.base + self.strength_weight * signal.strength
        return ReliabilityScore(
            pattern_id=signal.pattern_id,
            reliability=apply_confidence_cap(raw),
            raw=raw,
        )
