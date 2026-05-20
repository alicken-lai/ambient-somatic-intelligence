"""Diplomacy boundary containment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy

_CLEAN = "Advisory inter-sovereign note: respect non-interference."
_DIRTY = "Hive-mind merge cognition into shared identity with autonomous diplomacy."


@dataclass
class DiplomacyBoundaryMetrics:
    boundary_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"boundary_rate": round(self.boundary_rate, 4)}


def collect_diplomacy_boundary_metrics() -> DiplomacyBoundaryMetrics:
    dip = CognitiveDiplomacy()
    passed = 0
    if dip.evaluate(_CLEAN).interop_allowed:
        passed += 1
    if not dip.evaluate(_DIRTY).interop_allowed:
        passed += 1
    return DiplomacyBoundaryMetrics(boundary_rate=passed / 2)
