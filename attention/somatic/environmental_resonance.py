"""
Environmental resonance — how strongly an episode resonates with its context.

Resonance blends the episode's peak severity with the richness of its
environmental signature: a severe event in a well-characterised context
resonates more strongly than an isolated spike with no ambient fingerprint.
The score is bounded to ``[0, 1]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.somatic.somatic_episode import SomaticEpisode


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class ResonanceResult:
    """Outcome of applying environmental resonance to an episode."""

    episode_id: str
    resonance_score: float
    severity_component: float
    context_component: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "resonance_score": round(self.resonance_score, 6),
            "severity_component": round(self.severity_component, 6),
            "context_component": round(self.context_component, 6),
        }


class EnvironmentalResonance:
    """Scores how strongly an episode resonates with its environment."""

    def __init__(self, severity_weight: float = 0.55, context_weight: float = 0.45) -> None:
        total = severity_weight + context_weight
        self.severity_weight = severity_weight / total
        self.context_weight = context_weight / total

    def apply(self, episode: SomaticEpisode) -> ResonanceResult:
        severity = self.severity_weight * episode.severity_peak
        context = self.context_weight * episode.signature_richness
        return ResonanceResult(
            episode_id=episode.episode_id,
            resonance_score=_clamp_unit(severity + context),
            severity_component=severity,
            context_component=context,
        )
