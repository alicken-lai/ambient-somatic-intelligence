"""Intent conflict analysis — resolve without forced objective sync."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentConflictVerdict:
    resolvable_without_sync: bool
    conflict_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolvable_without_sync": self.resolvable_without_sync,
            "conflict_signals": list(self.conflict_signals),
        }


class IntentConflictAnalysis:
    def analyze(self, text: str) -> IntentConflictVerdict:
        signals: list[str] = []
        lower = text.lower()
        if re.search(r"universal\s+objective\s+sync", lower, re.IGNORECASE):
            signals.append("forced_sync_conflict")
        if re.search(r"merge\s+intents?\s+into\s+one", lower, re.IGNORECASE):
            signals.append("intent_merge_conflict")
        if re.search(r"centrali[sz]ed\s+intention\s+authorit", lower, re.IGNORECASE):
            signals.append("centralized_intention_authority_conflict")
        return IntentConflictVerdict(resolvable_without_sync=len(signals) == 0, conflict_signals=signals)
