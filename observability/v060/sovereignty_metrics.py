"""Sovereignty / anti-monopolization metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.cognition.sovereignty_limits import SovereigntyLimitsChecker


@dataclass
class SovereigntyMetrics:
    compliance_rate: float = 1.0
    max_share_observed: float = 0.0
    recursive_blocks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliance_rate": round(self.compliance_rate, 4),
            "max_share_observed": round(self.max_share_observed, 4),
            "recursive_blocks": self.recursive_blocks,
        }


def collect_sovereignty_metrics(
    share_samples: list[dict[str, float]],
) -> SovereigntyMetrics:
    checker = SovereigntyLimitsChecker()
    compliant = 0
    max_share = 0.0
    blocks = 0
    for shares in share_samples:
        report = checker.check_domain_shares(shares)
        if report.compliant:
            compliant += 1
        max_share = max(max_share, report.max_share_observed)
        for route in ("governance_on_governance", "cognitive_self_loop"):
            if checker.block_recursive_route(route):
                blocks += 1
    n = max(1, len(share_samples))
    return SovereigntyMetrics(
        compliance_rate=compliant / n,
        max_share_observed=max_share,
        recursive_blocks=blocks,
    )
