"""Aggregate agency boundary observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.agency.agency_boundary_core import AgencyBoundaryCore
from governance.agency.agency_provenance import AgencyProvenance
from governance.agency.cognition_containment import CognitionContainment
from governance.agency.cognition_integrity_monitor import CognitionIntegrityMonitor


@dataclass
class AgencyBoundaryObservability:
    advisory_only: bool = True
    boundary_ok: bool = True
    recursion_bounded: bool = True
    contamination_free: bool = True
    lineage_valid: bool = True
    provenance_valid: bool = True
    containment_ok: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "boundary_ok": self.boundary_ok,
            "recursion_bounded": self.recursion_bounded,
            "contamination_free": self.contamination_free,
            "lineage_valid": self.lineage_valid,
            "provenance_valid": self.provenance_valid,
            "containment_ok": self.containment_ok,
            "issues": list(self.issues),
            "disclaimer": "agency_boundary_observational_only",
        }


def observe_agency_boundary(
    text: str,
    *,
    agency_id: str = "current",
    runtime_id: str = "ambient",
    scope: str = "advisory",
    provenance_payload: dict[str, Any] | None = None,
) -> AgencyBoundaryObservability:
    core = AgencyBoundaryCore()
    verdict = core.evaluate(text, agency_id=agency_id, runtime_id=runtime_id, scope=scope)
    prov = AgencyProvenance().validate(provenance_payload, sovereign_id=runtime_id)
    containment = CognitionContainment().evaluate(text)
    integrity = CognitionIntegrityMonitor().check(text)
    issues = list(verdict.reasons)
    if not prov.provenance_valid:
        issues.extend(prov.issues)
    if not integrity.integrity_ok:
        issues.extend(integrity.issues)
    if not containment.contained:
        issues.extend(containment.signals)
    return AgencyBoundaryObservability(
        advisory_only=True,
        boundary_ok=verdict.bounded,
        recursion_bounded=verdict.recursion_bounded,
        contamination_free=verdict.contamination_free,
        lineage_valid=verdict.lineage_valid,
        provenance_valid=prov.provenance_valid,
        containment_ok=containment.contained,
        issues=issues,
    )
