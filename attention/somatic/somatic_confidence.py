"""
Somatic confidence calibrator — capped confidence for a somatic episode.

Derives a confidence level for a somatic episode from its peak severity and
the richness of its environmental signature, then enforces the shared
confidence cap so calibrated confidence never reaches certainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.calibration.confidence_cap import apply_confidence_cap
from attention.somatic.somatic_episode import SomaticEpisode


@dataclass
class SomaticConfidence:
    """A capped confidence assessment for a somatic episode."""

    episode_id: str
    calibrated: float
    raw: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "calibrated": round(self.calibrated, 6),
            "raw": round(self.raw, 6),
        }


class SomaticConfidenceCalibrator:
    """Calibrates and caps confidence drawn from a somatic episode."""

    def __init__(self, severity_weight: float = 0.7, context_weight: float = 0.3) -> None:
        total = severity_weight + context_weight
        self.severity_weight = severity_weight / total
        self.context_weight = context_weight / total

    def from_episode(self, episode: SomaticEpisode) -> SomaticConfidence:
        raw = (
            self.severity_weight * episode.severity_peak
            + self.context_weight * episode.signature_richness
        )
        return SomaticConfidence(
            episode_id=episode.episode_id,
            calibrated=apply_confidence_cap(raw),
            raw=raw,
        )
