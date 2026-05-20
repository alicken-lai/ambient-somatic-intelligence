"""Civilization semantic anchor — local interpretive anchor without centralized interpretation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.meaning.meaning_record import MeaningRecord


@dataclass
class SemanticAnchorVerdict:
    anchored: bool
    advisory_only: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchored": self.anchored,
            "advisory_only": self.advisory_only,
            "issues": list(self.issues),
        }


class CivilizationSemanticAnchor:
    def anchor(self, record: MeaningRecord) -> SemanticAnchorVerdict:
        issues: list[str] = []
        lower = record.summary.lower()
        if "centralized interpretation" in lower:
            issues.append("centralized_interpretation")
        if record.retention_hours > 8760 * 5:
            issues.append("retention_too_long")
        return SemanticAnchorVerdict(
            anchored=len(issues) == 0,
            issues=issues,
        )
