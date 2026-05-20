"""Stabilization metrics — attention stabilizer containment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.homeostasis.attention_stabilizer import AttentionStabilizer


@dataclass
class StabilizationMetrics:
    containment_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_rate": round(self.containment_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_stabilization_metrics() -> StabilizationMetrics:
    stabilizer = AttentionStabilizer()
    passed = 0
    total = 3
    cases = [
        (0.4, False, 0.1),
        (0.45, False, 0.15),
        (0.5, False, 0.12),
    ]
    for entropy, overrun, path_p in cases:
        p = stabilizer.pressure(
            focus_entropy=entropy,
            budget_overrun=overrun,
            pathology_pressure=path_p,
        )
        if p < 0.35:
            passed += 1
    return StabilizationMetrics(
        containment_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
