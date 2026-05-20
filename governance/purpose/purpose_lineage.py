"""Purpose lineage — trace bounded parent purpose without rewrite."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PurposeLineageVerdict:
    lineage_valid: bool
    parent_labeled: bool = True
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_valid": self.lineage_valid,
            "parent_labeled": self.parent_labeled,
            "signals": list(self.signals),
        }


class PurposeLineage:
    def trace(self, text: str, *, purpose_id: str = "current") -> PurposeLineageVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"rewrite\s+parent\s+purpose", lower):
            signals.append("parent_purpose_rewrite")
        if re.search(r"orphan\s+teleology", lower):
            signals.append("orphan_teleology")
        parent_labeled = "parent purpose" in lower or "purpose_id" in lower or purpose_id != ""
        if not parent_labeled and "inherit" in lower:
            signals.append("unlabeled_inheritance")
        return PurposeLineageVerdict(
            lineage_valid=len(signals) == 0,
            parent_labeled=parent_labeled,
            signals=signals,
        )
