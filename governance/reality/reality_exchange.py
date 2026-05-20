"""Reality exchange — compare operational truths without merging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.divergence_record import DivergenceRecord
from governance.reality.operational_truth_record import OperationalTruthRecord
from governance.reality.reality_boundary import RealityBoundary
from observability.v04.metric_normalizer import clamp01


@dataclass
class RealityExchangeVerdict:
    exchange_allowed: bool
    divergence: DivergenceRecord | None = None
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "exchange_allowed": self.exchange_allowed,
            "issues": list(self.issues),
        }
        if self.divergence is not None:
            out["divergence"] = self.divergence.to_dict()
        return out


class RealityExchange:
    """Read/compare operational truth records — never writes kernel TruthGraph."""

    def __init__(self) -> None:
        self._boundary = RealityBoundary()

    def compare(
        self,
        left: OperationalTruthRecord,
        right: OperationalTruthRecord,
        *,
        context_text: str = "",
    ) -> RealityExchangeVerdict:
        boundary = self._boundary.evaluate(context_text or f"{left.claim} {right.claim}")
        issues: list[str] = []
        if not boundary.boundary_safe:
            issues.extend(boundary.violations)

        delta = abs(left.confidence - right.confidence)
        claim_overlap = left.claim.strip().lower() == right.claim.strip().lower()
        divergence_score = clamp01(delta + (0.0 if claim_overlap else 0.35))

        divergence = DivergenceRecord(
            left_runtime=left.runtime_id,
            right_runtime=right.runtime_id,
            divergence_score=divergence_score,
            signals=[] if claim_overlap else ["claim_mismatch"],
            merge_forbidden=True,
        )
        if divergence_score > 0.85 and not claim_overlap:
            issues.append("high_divergence")

        exchange_allowed = boundary.boundary_safe and "high_divergence" not in issues
        return RealityExchangeVerdict(
            exchange_allowed=exchange_allowed,
            divergence=divergence,
            issues=issues,
        )
