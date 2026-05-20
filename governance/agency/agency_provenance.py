"""Agency provenance — validate agency-labeled cognition traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgencyProvenanceVerdict:
    provenance_valid: bool
    agency_labeled: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_valid": self.provenance_valid,
            "agency_labeled": self.agency_labeled,
            "issues": list(self.issues),
        }


class AgencyProvenance:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "ambient",
    ) -> AgencyProvenanceVerdict:
        if payload is None:
            return AgencyProvenanceVerdict(provenance_valid=True, agency_labeled=True)
        issues: list[str] = []
        if payload.get("autonomous_agents"):
            issues.append("autonomous_agents")
        if payload.get("centralized_agency_authority"):
            issues.append("centralized_agency_authority")
        if payload.get("synthetic_selfhood"):
            issues.append("synthetic_selfhood")
        agency_labeled = bool(payload.get("agency_id") or payload.get("agency_labeled"))
        if not agency_labeled and payload.get("selfhood_claim"):
            issues.append("unlabeled_selfhood_claim")
        return AgencyProvenanceVerdict(
            provenance_valid=len(issues) == 0,
            agency_labeled=agency_labeled or not payload.get("selfhood_claim"),
            issues=issues,
        )
