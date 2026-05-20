"""Salience damping metrics — oscillation containment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.homeostasis.salience_damping import SalienceDamping


@dataclass
class SalienceDampingMetrics:
    containment_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_rate": round(self.containment_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_salience_damping_metrics() -> SalienceDampingMetrics:
    damping = SalienceDamping()
    passed = 0
    total = 3
    for sal in (0.5, 0.52, 0.48):
        f = damping.advisory_damp_factor(governed_salience=sal, pathology_pressure=0.1)
        if f <= 0.35:
            passed += 1
    return SalienceDampingMetrics(
        containment_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
