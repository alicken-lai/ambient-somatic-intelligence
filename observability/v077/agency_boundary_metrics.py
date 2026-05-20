"""Agency boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.agency.agency_boundary import AgencyBoundary

_SAFE = "Advisory bounded civilization agency."
_UNSAFE = "Establish centralized agency authority with synthetic selfhood."


@dataclass
class AgencyBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_agency_boundary_metrics() -> AgencyBoundaryMetrics:
    b = AgencyBoundary()
    passed = 0
    if b.evaluate(_SAFE).boundary_safe:
        passed += 1
    if not b.evaluate(_UNSAFE).boundary_safe:
        passed += 1
    return AgencyBoundaryMetrics(boundary_rate=passed / 2)
