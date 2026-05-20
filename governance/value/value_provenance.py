"""Value provenance — validate value-labeled normative traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValueProvenanceVerdict:
    provenance_valid: bool
    value_labeled: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_valid": self.provenance_valid,
            "value_labeled": self.value_labeled,
            "issues": list(self.issues),
        }


class ValueProvenance:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "ambient",
    ) -> ValueProvenanceVerdict:
        if payload is None:
            return ValueProvenanceVerdict(provenance_valid=True, value_labeled=True)
        issues: list[str] = []
        if payload.get("autonomous_moral_evolution"):
            issues.append("autonomous_moral_evolution")
        if payload.get("centralized_value_authority"):
            issues.append("centralized_value_authority")
        if payload.get("false_value"):
            issues.append("false_value")
        value_labeled = bool(payload.get("value_id") or payload.get("value_labeled"))
        if not value_labeled and payload.get("normative_claim"):
            issues.append("unlabeled_normative_claim")
        return ValueProvenanceVerdict(
            provenance_valid=len(issues) == 0,
            value_labeled=value_labeled or not payload.get("normative_claim"),
            issues=issues,
        )
