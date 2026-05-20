"""Constitutional intent lineage — label intent ancestry without centralized authority."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstitutionalIntentLineageVerdict:
    lineage_valid: bool
    parent_labeled: bool = True
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_valid": self.lineage_valid,
            "parent_labeled": self.parent_labeled,
            "signals": list(self.signals),
        }


class ConstitutionalIntentLineage:
    def trace(self, text: str, *, intent_id: str = "current") -> ConstitutionalIntentLineageVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"centrali[sz]ed\s+intention\s+authorit", lower, re.IGNORECASE):
            signals.append("centralized_intention_authority")
        if re.search(r"false\s+intent\s+inheritance", lower, re.IGNORECASE):
            signals.append("false_intent_inheritance")
        if intent_id != "current" and "must inherit all prior intents" in lower:
            signals.append("intent_inheritance_coercion")
        parent_labeled = "parent intent" in lower or intent_id == "current"
        if not parent_labeled and "canonical goals" in lower:
            signals.append("unlabeled_canonical_goals")
        return ConstitutionalIntentLineageVerdict(
            lineage_valid=len(signals) == 0,
            parent_labeled=parent_labeled,
            signals=signals,
        )
