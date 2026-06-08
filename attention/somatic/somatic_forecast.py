"""
Somatic forecast — projects an episode's resonance forward in time.

Wraps :class:`EnvironmentalResonance` to produce a single forward-looking
resonance projection for an episode, bounded to ``[0, 1]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.somatic.environmental_resonance import EnvironmentalResonance
from attention.somatic.somatic_episode import SomaticEpisode


@dataclass
class SomaticForecastPoint:
    """A single forward resonance projection for an episode."""

    episode_id: str
    resonance_projected: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "resonance_projected": round(self.resonance_projected, 6),
        }


class SomaticForecast:
    """Projects an episode's resonance forward."""

    def __init__(self, resonance: EnvironmentalResonance | None = None) -> None:
        self._resonance = resonance or EnvironmentalResonance()

    def forecast_episode(self, episode: SomaticEpisode) -> SomaticForecastPoint:
        result = self._resonance.apply(episode)
        return SomaticForecastPoint(
            episode_id=episode.episode_id,
            resonance_projected=result.resonance_score,
        )
