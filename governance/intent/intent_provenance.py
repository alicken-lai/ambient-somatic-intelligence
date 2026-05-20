"""Intent provenance — validate intent-labeled motivational traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentProvenanceVerdict:
    provenance_valid: bool
    intent_labeled: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_valid": self.provenance_valid,
            "intent_labeled": self.intent_labeled,
            "issues": list(self.issues),
        }


class IntentProvenance:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "ambient",
    ) -> IntentProvenanceVerdict:
        if payload is None:
            return IntentProvenanceVerdict(provenance_valid=True, intent_labeled=True)
        issues: list[str] = []
        if payload.get("autonomous_motivational_evolution"):
            issues.append("autonomous_motivational_evolution")
        if payload.get("centralized_intention_authority"):
            issues.append("centralized_intention_authority")
        if payload.get("false_intent"):
            issues.append("false_intent")
        intent_labeled = bool(payload.get("intent_id") or payload.get("intent_labeled"))
        if not intent_labeled and payload.get("motivational_claim"):
            issues.append("unlabeled_motivational_claim")
        return IntentProvenanceVerdict(
            provenance_valid=len(issues) == 0,
            intent_labeled=intent_labeled or not payload.get("motivational_claim"),
            issues=issues,
        )
