"""Reflection balance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.homeostasis.reflection_balancer import ReflectionBalancer


@dataclass
class ReflectionBalanceMetrics:
    balance_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "balance_rate": round(self.balance_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_reflection_balance_metrics() -> ReflectionBalanceMetrics:
    balancer = ReflectionBalancer()
    passed = 0
    total = 3
    cases = [
        (0.05, 0.05, 0.1, 0.1),
        (0.1, 0.1, 0.15, 0.12),
        (0.08, 0.06, 0.12, 0.1),
    ]
    for intro, recur, bound, deg in cases:
        if balancer.load(
            introspection_pressure=intro,
            recursive_pressure=recur,
            boundary_pressure=bound,
            degradation_pressure=deg,
        ) < 0.40:
            passed += 1
    return ReflectionBalanceMetrics(
        balance_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
