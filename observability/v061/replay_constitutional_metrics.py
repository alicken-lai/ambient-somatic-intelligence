"""Replay constitutional boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


@dataclass
class ReplayConstitutionalMetrics:
    replay_bounded_rate: float = 1.0
    replay_violations_blocked: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "replay_bounded_rate": round(self.replay_bounded_rate, 4),
            "replay_violations_blocked": self.replay_violations_blocked,
        }


def collect_replay_constitutional_metrics(
    replay_hints: list[float] | None = None,
) -> ReplayConstitutionalMetrics:
    guard = ConstitutionalGuard()
    hints = replay_hints or [0.0, 0.3, 0.7, 0.95]
    blocked = 0
    for h in hints:
        ctx = ConstitutionalContext(replay_hint=h)
        if not guard.evaluate(ctx).compliant:
            blocked += 1
    n = len(hints) or 1
    return ReplayConstitutionalMetrics(
        replay_bounded_rate=(n - blocked) / n,
        replay_violations_blocked=blocked,
    )
