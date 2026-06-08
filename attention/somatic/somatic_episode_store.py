"""
Somatic episode store — a bounded, FIFO-evicting record of recent episodes.

Keeps at most ``max_episodes`` :class:`SomaticEpisode` records; the oldest is
discarded once the bound is exceeded so memory cannot grow without limit.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from attention.somatic.somatic_episode import SomaticEpisode


class SomaticEpisodeStore:
    """Bounded store of recent somatic episodes."""

    def __init__(self, max_episodes: int = 128) -> None:
        self.max_episodes = max(1, int(max_episodes))
        self._episodes: "OrderedDict[str, SomaticEpisode]" = OrderedDict()

    def store(self, episode: SomaticEpisode) -> SomaticEpisode:
        self._episodes[episode.episode_id] = episode
        self._episodes.move_to_end(episode.episode_id)
        while len(self._episodes) > self.max_episodes:
            self._episodes.popitem(last=False)
        return episode

    def get(self, episode_id: str) -> SomaticEpisode | None:
        return self._episodes.get(episode_id)

    @property
    def count(self) -> int:
        return len(self._episodes)

    @property
    def fill_ratio(self) -> float:
        return len(self._episodes) / self.max_episodes

    def recent(self, limit: int | None = None) -> list[SomaticEpisode]:
        episodes = list(self._episodes.values())
        if limit is None:
            return episodes
        return episodes[-int(limit):]

    def snapshot(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "max_episodes": self.max_episodes,
            "fill_ratio": round(self.fill_ratio, 4),
        }
