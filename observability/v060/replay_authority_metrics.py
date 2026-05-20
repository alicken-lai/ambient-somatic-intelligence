"""Replay authority bounded influence metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.cognition.replay_authority import REPLAY_MAX_INFLUENCE, ReplayAuthority


@dataclass
class ReplayAuthorityMetrics:
    bounded_rate: float = 1.0
    mean_replay_weight: float = 0.0
    max_replay_weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded_rate": round(self.bounded_rate, 4),
            "mean_replay_weight": round(self.mean_replay_weight, 4),
            "max_replay_weight": round(self.max_replay_weight, 4),
            "replay_max_influence": REPLAY_MAX_INFLUENCE,
        }


def collect_replay_authority_metrics(
    live_replay_pairs: list[tuple[float, float]],
) -> ReplayAuthorityMetrics:
    auth = ReplayAuthority()
    weights: list[float] = []
    bounded = 0
    for live, hint in live_replay_pairs:
        r = auth.blend(live, hint, replay_confidence=0.6)
        weights.append(r.replay_weight)
        if r.bounded:
            bounded += 1
    n = max(1, len(live_replay_pairs))
    return ReplayAuthorityMetrics(
        bounded_rate=bounded / n,
        mean_replay_weight=sum(weights) / max(1, len(weights)) if weights else 0.0,
        max_replay_weight=max(weights) if weights else 0.0,
    )
