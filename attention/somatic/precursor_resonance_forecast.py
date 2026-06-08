"""
Precursor resonance forecast — projects how precursor signals may resonate.

Given an episode and a set of early :class:`PrecursorSignal` indicators, this
forecaster estimates, per precursor, how strongly that precursor is likely to
resonate with the episode's severity.  Returns a list of per-precursor
projections (possibly empty).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.core.precursor_signal import PrecursorSignal
from attention.somatic.somatic_episode import SomaticEpisode


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class PrecursorResonanceProjection:
    """Projected resonance of one precursor against an episode."""

    pattern_id: str
    projected_resonance: float
    precursor_strength: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "projected_resonance": round(self.projected_resonance, 6),
            "precursor_strength": round(self.precursor_strength, 6),
        }


class PrecursorResonanceForecaster:
    """Forecasts per-precursor resonance against a somatic episode."""

    def __init__(self, severity_weight: float = 0.5, strength_weight: float = 0.5) -> None:
        total = severity_weight + strength_weight
        self.severity_weight = severity_weight / total
        self.strength_weight = strength_weight / total

    def forecast(
        self,
        episode: SomaticEpisode,
        precursors: list[PrecursorSignal],
    ) -> list[PrecursorResonanceProjection]:
        projections: list[PrecursorResonanceProjection] = []
        for signal in precursors:
            projected = _clamp_unit(
                self.severity_weight * episode.severity_peak
                + self.strength_weight * signal.strength
            )
            projections.append(
                PrecursorResonanceProjection(
                    pattern_id=signal.pattern_id,
                    projected_resonance=projected,
                    precursor_strength=signal.strength,
                )
            )
        return projections
