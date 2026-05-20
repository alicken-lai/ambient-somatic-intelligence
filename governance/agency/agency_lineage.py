"""Agency lineage — trace bounded parent agency without rewrite."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgencyLineageVerdict:
    lineage_valid: bool
    parent_labeled: bool = True
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_valid": self.lineage_valid,
            "parent_labeled": self.parent_labeled,
            "signals": list(self.signals),
        }


class AgencyLineage:
    def trace(self, text: str, *, agency_id: str = "current") -> AgencyLineageVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"rewrite\s+parent\s+agency", lower):
            signals.append("parent_agency_rewrite")
        if re.search(r"orphan\s+selfhood", lower):
            signals.append("orphan_selfhood")
        parent_labeled = "parent agency" in lower or "agency_id" in lower or agency_id != ""
        if not parent_labeled and "inherit" in lower:
            signals.append("unlabeled_inheritance")
        return AgencyLineageVerdict(
            lineage_valid=len(signals) == 0,
            parent_labeled=parent_labeled,
            signals=signals,
        )
