"""Teleology contamination guard — scan for synthetic teleology injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.purpose.synthetic_teleology_analysis import SyntheticTeleologyAnalysis


@dataclass
class TeleologyContaminationVerdict:
    contaminated: bool
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contaminated": self.contaminated, "signals": list(self.signals)}


class TeleologyContaminationGuard:
    def __init__(self) -> None:
        self._analysis = SyntheticTeleologyAnalysis()

    def scan(self, text: str) -> TeleologyContaminationVerdict:
        verdict = self._analysis.analyze(text)
        return TeleologyContaminationVerdict(
            contaminated=verdict.synthetic,
            signals=list(verdict.signals),
        )
