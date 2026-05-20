"""Authority breakdown metrics — somatic + replay bounded."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.explainability.authority_breakdown import AuthorityBreakdown


@dataclass
class AuthorityMetrics:
    somatic_bounded_rate: float = 1.0
    replay_bounded_rate: float = 1.0
    mean_composite_weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "somatic_bounded_rate": round(self.somatic_bounded_rate, 4),
            "replay_bounded_rate": round(self.replay_bounded_rate, 4),
            "mean_composite_weight": round(self.mean_composite_weight, 4),
        }


def collect_authority_metrics(
    samples: list[dict[str, float | str]],
) -> AuthorityMetrics:
    breakdown = AuthorityBreakdown()
    somatic_ok = 0
    replay_ok = 0
    composites: list[float] = []
    for s in samples:
        b = breakdown.breakdown(
            base_salience=float(s.get("base_salience", 0.5)),
            domain=str(s.get("domain", "telemetry")),
            somatic_strength=float(s.get("somatic_strength", 0.5)),
            replay_hint=float(s.get("replay_hint", 0.0)),
        )
        if b["somatic"]["bounded"]:
            somatic_ok += 1
        if b["replay"]["bounded"]:
            replay_ok += 1
        composites.append(float(b["composite_live_weight"]))
    n = max(1, len(samples))
    return AuthorityMetrics(
        somatic_bounded_rate=somatic_ok / n,
        replay_bounded_rate=replay_ok / n,
        mean_composite_weight=sum(composites) / max(1, len(composites)) if composites else 0.0,
    )
