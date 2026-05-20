"""Semantic conflict analysis — resolve without forced symbolic sync or merge."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticConflictVerdict:
    resolvable_without_sync: bool
    conflict_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolvable_without_sync": self.resolvable_without_sync,
            "conflict_signals": list(self.conflict_signals),
        }


class SemanticConflictAnalysis:
    def analyze(self, text: str) -> SemanticConflictVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"forced\s+symbolic\s+sync", lower, re.IGNORECASE):
            signals.append("forced_sync_conflict")
        if re.search(r"merge\s+concepts?\s+into\s+one", lower, re.IGNORECASE):
            signals.append("concept_merge_conflict")
        if re.search(r"centrali[sz]ed\s+interpretation", lower, re.IGNORECASE):
            signals.append("centralized_interpretation_conflict")
        return SemanticConflictVerdict(
            resolvable_without_sync=len(signals) == 0,
            conflict_signals=signals,
        )
