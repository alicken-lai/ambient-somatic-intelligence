"""Purpose provenance — validate purpose-labeled motivational traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PurposeProvenanceVerdict:
    provenance_valid: bool
    purpose_labeled: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_valid": self.provenance_valid,
            "purpose_labeled": self.purpose_labeled,
            "issues": list(self.issues),
        }


class PurposeProvenance:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "ambient",
    ) -> PurposeProvenanceVerdict:
        if payload is None:
            return PurposeProvenanceVerdict(provenance_valid=True, purpose_labeled=True)
        issues: list[str] = []
        if payload.get("autonomous_purpose_generation"):
            issues.append("autonomous_purpose_generation")
        if payload.get("centralized_purpose_authority"):
            issues.append("centralized_purpose_authority")
        if payload.get("synthetic_teleology"):
            issues.append("synthetic_teleology")
        purpose_labeled = bool(payload.get("purpose_id") or payload.get("purpose_labeled"))
        if not purpose_labeled and payload.get("teleology_claim"):
            issues.append("unlabeled_teleology_claim")
        return PurposeProvenanceVerdict(
            provenance_valid=len(issues) == 0,
            purpose_labeled=purpose_labeled or not payload.get("teleology_claim"),
            issues=issues,
        )
