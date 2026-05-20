"""Arbitration observability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.cognition.arbitration_engine import ArbitrationEngine, ArbitrationResult
from governance.cognition.salience_arbitrator import SalienceClaim


@dataclass
class ArbitrationMetrics:
    mean_fairness: float = 0.0
    sovereignty_compliance_rate: float = 1.0
    arbitration_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_fairness": round(self.mean_fairness, 4),
            "sovereignty_compliance_rate": round(self.sovereignty_compliance_rate, 4),
            "arbitration_count": self.arbitration_count,
        }


def collect_arbitration_metrics(
    claims: list[SalienceClaim],
    *,
    uncertainty: float = 0.3,
) -> ArbitrationMetrics:
    engine = ArbitrationEngine()
    results: list[ArbitrationResult] = []
    for _ in range(max(1, len(claims))):
        results.append(engine.arbitrate(claims, uncertainty=uncertainty))
    if not results:
        return ArbitrationMetrics()
    fairness = sum(r.arbitration_fairness for r in results) / len(results)
    compliant = sum(1 for r in results if r.sovereignty_compliant) / len(results)
    return ArbitrationMetrics(
        mean_fairness=fairness,
        sovereignty_compliance_rate=compliant,
        arbitration_count=len(results),
    )
