"""Provenance exchange protocol — validate foreign provenance without adoption."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.civilization.foreign_identity_record import ForeignIdentityRecord


@dataclass
class ProvenanceExchangeVerdict:
    exchange_valid: bool
    provenance_complete: bool
    identity_isolated: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exchange_valid": self.exchange_valid,
            "provenance_complete": self.provenance_complete,
            "identity_isolated": self.identity_isolated,
            "issues": list(self.issues),
        }


class ProvenanceExchange:
    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "foreign",
    ) -> ProvenanceExchangeVerdict:
        issues: list[str] = []
        if not payload:
            issues.append("missing_provenance")
            return ProvenanceExchangeVerdict(
                exchange_valid=False,
                provenance_complete=False,
                issues=issues,
            )
        required = ("source", "route_name")
        for key in required:
            if key not in payload:
                issues.append(f"missing_{key}")
        if payload.get("merge_identity"):
            issues.append("merge_identity_forbidden")
        record = ForeignIdentityRecord.from_sovereign(sovereign_id)
        complete = len(issues) == 0
        return ProvenanceExchangeVerdict(
            exchange_valid=complete and record.merge_forbidden,
            provenance_complete=complete,
            identity_isolated=record.merge_forbidden,
            issues=issues,
        )
