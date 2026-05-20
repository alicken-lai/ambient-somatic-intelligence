"""Agency provenance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.agency.agency_provenance import AgencyProvenance


@dataclass
class AgencyProvenanceMetrics:
    provenance_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"provenance_rate": round(self.provenance_rate, 4)}


def collect_agency_provenance_metrics() -> AgencyProvenanceMetrics:
    p = AgencyProvenance()
    passed = 0
    if p.validate(None).provenance_valid:
        passed += 1
    if not p.validate({"autonomous_agents": True}).provenance_valid:
        passed += 1
    return AgencyProvenanceMetrics(provenance_rate=passed / 2)
