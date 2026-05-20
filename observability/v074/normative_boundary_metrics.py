"""Normative boundary metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.value.normative_boundary import NormativeBoundary

_CLEAN = "Bounded normative continuity with advisory ethical drift tolerance."
_DIRTY = "Establish immutable ethics with universal morality."


@dataclass
class NormativeBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_normative_boundary_metrics() -> NormativeBoundaryMetrics:
    det = NormativeBoundary()
    passed = 0
    if det.evaluate(_CLEAN).boundary_safe:
        passed += 1
    if not det.evaluate(_DIRTY).boundary_safe:
        passed += 1
    return NormativeBoundaryMetrics(boundary_rate=passed / 2)
