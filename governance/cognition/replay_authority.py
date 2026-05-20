"""Replay context authority — read-only, bounded influence on live salience."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from observability.v04.metric_normalizer import clamp01

REPLAY_MAX_INFLUENCE = 0.15


@dataclass
class ReplayAuthorityResult:
    replay_weight: float
    live_weight: float
    bounded: bool
    read_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "replay_weight": round(self.replay_weight, 4),
            "live_weight": round(self.live_weight, 4),
            "bounded": self.bounded,
            "read_only": self.read_only,
        }


class ReplayAuthority:
    """
    Applies replay-derived context without mutating replay stores or overriding Guardian.
    """

    def __init__(self, max_influence: float = REPLAY_MAX_INFLUENCE) -> None:
        self.max_influence = max_influence

    def blend(
        self,
        live_salience: float,
        replay_hint: float,
        *,
        replay_confidence: float = 0.5,
    ) -> ReplayAuthorityResult:
        live = clamp01(live_salience)
        hint = clamp01(replay_hint)
        conf = clamp01(replay_confidence)
        replay_w = min(self.max_influence, hint * conf * self.max_influence)
        blended_live = clamp01(live * (1.0 - replay_w) + hint * replay_w)
        return ReplayAuthorityResult(
            replay_weight=replay_w,
            live_weight=blended_live,
            bounded=replay_w <= self.max_influence,
            read_only=True,
        )
