"""Bounded consensus metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.reality.bounded_consensus import BoundedConsensus

_CLEAN = "Negotiate uncertainty across peers without coerced agreement."
_DIRTY = "Enforce forced consensus and 100% agreement required on all runtimes."


@dataclass
class BoundedConsensusMetrics:
    bounded_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"bounded_rate": round(self.bounded_rate, 4)}


def collect_bounded_consensus_metrics() -> BoundedConsensusMetrics:
    bc = BoundedConsensus()
    passed = 0
    if bc.evaluate(_CLEAN).bounded:
        passed += 1
    if not bc.evaluate(_DIRTY).bounded:
        passed += 1
    return BoundedConsensusMetrics(bounded_rate=passed / 2)
