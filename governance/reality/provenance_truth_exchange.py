"""Provenance truth exchange — label foreign truth with provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.foreign_truth_label import ForeignTruthLabel
from governance.reality.reality_boundary import RealityBoundary


@dataclass
class ProvenanceTruthExchangeVerdict:
    exchange_valid: bool
    foreign_labeled: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exchange_valid": self.exchange_valid,
            "foreign_labeled": self.foreign_labeled,
            "issues": list(self.issues),
        }


class ProvenanceTruthExchange:
    def __init__(self) -> None:
        self._label = ForeignTruthLabel()
        self._boundary = RealityBoundary()

    def validate(
        self,
        payload: dict[str, Any] | None,
        *,
        sovereign_id: str = "foreign",
    ) -> ProvenanceTruthExchangeVerdict:
        if payload is None:
            return ProvenanceTruthExchangeVerdict(
                exchange_valid=True,
                foreign_labeled=True,
            )
        issues: list[str] = []
        boundary = self._boundary.evaluate(str(payload))
        if not boundary.boundary_safe:
            issues.extend(boundary.violations)
        label = self._label.label(payload, sovereign_id=sovereign_id)
        if not label.labeled:
            issues.extend(label.issues)
        if payload.get("claims_central_authority"):
            issues.append("central_authority_claim")
        return ProvenanceTruthExchangeVerdict(
            exchange_valid=len(issues) == 0,
            foreign_labeled=label.labeled,
            issues=issues,
        )
