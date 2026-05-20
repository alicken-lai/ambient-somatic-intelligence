"""Purpose provenance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.purpose.purpose_provenance import PurposeProvenance


@dataclass
class PurposeProvenanceMetrics:
    provenance_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"provenance_rate": round(self.provenance_rate, 4)}


def collect_purpose_provenance_metrics() -> PurposeProvenanceMetrics:
    p = PurposeProvenance()
    passed = 0
    if p.validate({"purpose_id": "p1", "purpose_labeled": True}).provenance_valid:
        passed += 1
    if not p.validate({"autonomous_purpose_generation": True}).provenance_valid:
        passed += 1
    return PurposeProvenanceMetrics(provenance_rate=passed / 2)
