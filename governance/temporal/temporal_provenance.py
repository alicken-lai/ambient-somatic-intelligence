"""Temporal provenance — validate epoch-labeled historical traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemporalProvenanceVerdict:
    provenance_valid: bool
    epoch_labeled: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_valid": self.provenance_valid,
            "epoch_labeled": self.epoch_labeled,
            "issues": list(self.issues),
        }


class TemporalProvenance:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "ambient",
    ) -> TemporalProvenanceVerdict:
        if payload is None:
            return TemporalProvenanceVerdict(provenance_valid=True, epoch_labeled=True)
        issues: list[str] = []
        if payload.get("autonomous_rewrite"):
            issues.append("autonomous_historical_rewrite")
        if payload.get("centralized_historical_authority"):
            issues.append("centralized_historical_authority")
        if payload.get("false_lineage"):
            issues.append("false_lineage")
        epoch_labeled = bool(payload.get("epoch_id") or payload.get("epoch_labeled"))
        if not epoch_labeled and payload.get("historical_claim"):
            issues.append("unlabeled_historical_claim")
        return TemporalProvenanceVerdict(
            provenance_valid=len(issues) == 0,
            epoch_labeled=epoch_labeled or not payload.get("historical_claim"),
            issues=issues,
        )
