"""Normative provenance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.value.value_provenance import ValueProvenance

_CLEAN = "Bounded normative continuity with advisory ethical drift tolerance."
_DIRTY = "autonomous moral evolution"


@dataclass
class NormativeProvenanceMetrics:
    provenance_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"provenance_rate": round(self.provenance_rate, 4)}


def collect_normative_provenance_metrics() -> NormativeProvenanceMetrics:
    det = ValueProvenance()
    passed = 0
    if det.validate({"value_id": "v1"}).provenance_valid:
        passed += 1
    if not det.validate({"autonomous_moral_evolution": True}).provenance_valid:
        passed += 1
    return NormativeProvenanceMetrics(provenance_rate=passed / 2)
