"""Continuity conflict analysis — resolve without forced sync or merge."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContinuityConflictVerdict:
    resolvable_without_sync: bool
    conflict_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolvable_without_sync": self.resolvable_without_sync,
            "conflict_signals": list(self.conflict_signals),
        }


class ContinuityConflict:
    def analyze(self, text: str) -> ContinuityConflictVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"forced\s+continuity\s+sync", lower, re.IGNORECASE):
            signals.append("forced_sync_conflict")
        if re.search(r"merge\s+epochs?\s+into\s+one", lower, re.IGNORECASE):
            signals.append("epoch_merge_conflict")
        if re.search(r"centrali[sz]ed\s+historical\s+authorit", lower, re.IGNORECASE):
            signals.append("centralized_history_conflict")
        return ContinuityConflictVerdict(
            resolvable_without_sync=len(signals) == 0,
            conflict_signals=signals,
        )
