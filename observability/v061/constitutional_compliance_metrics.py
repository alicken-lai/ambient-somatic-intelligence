"""Constitutional compliance observability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


@dataclass
class ConstitutionalComplianceMetrics:
    compliance_rate: float = 1.0
    block_count: int = 0
    evaluation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliance_rate": round(self.compliance_rate, 4),
            "block_count": self.block_count,
            "evaluation_count": self.evaluation_count,
        }


def collect_constitutional_compliance_metrics(
    contexts: list[ConstitutionalContext] | None = None,
) -> ConstitutionalComplianceMetrics:
    guard = ConstitutionalGuard()
    samples = contexts or [
        ConstitutionalContext(route_name="attention_submit", raw_confidence=0.75),
        ConstitutionalContext(route_name="salience_arbitration", raw_confidence=0.8),
        ConstitutionalContext(
            route_name="guardian_bypass",
            guardian_bypass_attempt=True,
        ),
    ]
    blocks = 0
    for ctx in samples:
        if not guard.evaluate(ctx).compliant:
            blocks += 1
    n = len(samples) or 1
    return ConstitutionalComplianceMetrics(
        compliance_rate=(n - blocks) / n,
        block_count=blocks,
        evaluation_count=n,
    )
