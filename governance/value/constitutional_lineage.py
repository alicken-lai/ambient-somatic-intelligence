"""Constitutional lineage — label value ancestry without centralized authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstitutionalLineageVerdict:
    lineage_valid: bool
    parent_labeled: bool = True
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_valid": self.lineage_valid,
            "parent_labeled": self.parent_labeled,
            "signals": list(self.signals),
        }


class ConstitutionalLineage:
    def trace(self, text: str, *, value_id: str = "current") -> ConstitutionalLineageVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"centrali[sz]ed\s+value\s+authorit", lower, re.IGNORECASE):
            signals.append("centralized_value_authority")
        if re.search(r"false\s+value\s+inheritance", lower, re.IGNORECASE):
            signals.append("false_value_inheritance")
        if value_id != "current" and "must inherit all prior values" in lower:
            signals.append("value_inheritance_coercion")
        parent_labeled = "parent value" in lower or value_id == "current"
        if not parent_labeled and "canonical ethics" in lower:
            signals.append("unlabeled_canonical_ethics")
        return ConstitutionalLineageVerdict(
            lineage_valid=len(signals) == 0,
            parent_labeled=parent_labeled,
            signals=signals,
        )
