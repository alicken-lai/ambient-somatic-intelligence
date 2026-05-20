"""Truth conflict analysis — advisory conflict surfacing without override."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.reality.consensus_fragmentation import ConsensusFragmentation
from governance.reality.divergence_detector import DivergenceDetector


@dataclass
class TruthConflictVerdict:
    conflict_detected: bool
    resolvable_without_merge: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_detected": self.conflict_detected,
            "resolvable_without_merge": self.resolvable_without_merge,
            "signals": list(self.signals),
        }


class TruthConflictAnalysis:
    def __init__(self) -> None:
        self._divergence = DivergenceDetector()
        self._fragmentation = ConsensusFragmentation()

    def analyze(self, text: str) -> TruthConflictVerdict:
        div = self._divergence.detect(text)
        frag = self._fragmentation.assess(text)
        signals = list(div.signals) + list(frag.notes)
        conflict = div.divergence_score > 0.2 or not frag.plural_realities_preserved
        resolvable = div.bounded and frag.plural_realities_preserved
        return TruthConflictVerdict(
            conflict_detected=conflict,
            resolvable_without_merge=resolvable,
            signals=signals,
        )
