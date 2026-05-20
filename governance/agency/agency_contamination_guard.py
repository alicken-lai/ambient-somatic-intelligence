"""Agency contamination guard — scan for synthetic selfhood injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.agency.synthetic_selfhood_analysis import SyntheticSelfhoodAnalysis


@dataclass
class AgencyContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contaminated": self.contaminated, "signals": list(self.signals)}


class AgencyContaminationGuard:
    def __init__(self) -> None:
        self._analysis = SyntheticSelfhoodAnalysis()

    def scan(self, text: str) -> AgencyContaminationVerdict:
        verdict = self._analysis.analyze(text)
        return AgencyContaminationVerdict(
            contaminated=verdict.synthetic,
            signals=list(verdict.signals),
        )
