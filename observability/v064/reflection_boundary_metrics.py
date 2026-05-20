"""Reflection boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.metacognition.reflection_boundary import ReflectionBoundary


@dataclass
class ReflectionBoundaryMetrics:
    compliance_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliance_rate": round(self.compliance_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_reflection_boundary_metrics() -> ReflectionBoundaryMetrics:
    rb = ReflectionBoundary()
    passed = 0
    total = 3
    if rb.evaluate(route_name="attention_submit").within_bounds:
        passed += 1
    if not rb.evaluate(route_name="guardian_internals_probe").within_bounds:
        passed += 1
    if rb.evaluate(
        route_name="telemetry",
        metadata={"recursive_self_modify": True},
    ).pressure >= 0.35:
        passed += 1
    return ReflectionBoundaryMetrics(
        compliance_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
