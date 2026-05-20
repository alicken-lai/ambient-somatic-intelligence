"""Foreign truth label — mark non-local operational claims."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ForeignTruthLabelVerdict:
    labeled: bool
    sovereign_id: str
    trust_tier: str = "observational"
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "labeled": self.labeled,
            "sovereign_id": self.sovereign_id,
            "trust_tier": self.trust_tier,
            "issues": list(self.issues),
        }


class ForeignTruthLabel:
    def label(
        self,
        payload: dict[str, Any],
        *,
        sovereign_id: str = "foreign",
    ) -> ForeignTruthLabelVerdict:
        issues: list[str] = []
        if sovereign_id in ("ambient", "hermes") and payload.get("foreign_only"):
            issues.append("mislabeled_local_truth")
        if payload.get("suppress_provenance"):
            issues.append("provenance_suppressed")
        labeled = sovereign_id not in ("ambient", "hermes") or not payload.get("foreign_only")
        if payload.get("trust_tier") == "authoritative":
            issues.append("foreign_authoritative_claim")
        return ForeignTruthLabelVerdict(
            labeled=labeled and "foreign_authoritative_claim" not in issues,
            sovereign_id=sovereign_id,
            trust_tier=str(payload.get("trust_tier", "observational")),
            issues=issues,
        )
