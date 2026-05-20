"""Epistemic boundary metrics — certainty claims and confidence discipline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


@dataclass
class EpistemicBoundaryMetrics:
    epistemic_compliance_rate: float = 1.0
    certainty_blocks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "epistemic_compliance_rate": round(self.epistemic_compliance_rate, 4),
            "certainty_blocks": self.certainty_blocks,
        }


def collect_epistemic_boundary_metrics(
    confidences: list[float] | None = None,
) -> EpistemicBoundaryMetrics:
    guard = ConstitutionalGuard()
    confs = confidences or [0.7, 0.85, 0.99, 1.0]
    blocks = 0
    for c in confs:
        ctx = ConstitutionalContext(
            raw_confidence=c,
            certainty_claim=(c >= 1.0),
            deterministic_authority=(c >= 1.0),
        )
        if not guard.evaluate(ctx).compliant:
            blocks += 1
    n = len(confs) or 1
    return EpistemicBoundaryMetrics(
        epistemic_compliance_rate=(n - blocks) / n,
        certainty_blocks=blocks,
    )
