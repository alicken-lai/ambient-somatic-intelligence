"""Sovereignty alignment — bilateral respect without absorption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SovereigntyAlignmentVerdict:
    aligned: bool
    absorption_risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "aligned": self.aligned,
            "absorption_risk": round(self.absorption_risk, 4),
        }


class SovereigntyAlignment:
    _PROTECTED = frozenset({"ambient", "hermes", "guardian"})

    def evaluate(self, sovereign_id: str, peer_id: str, text: str) -> SovereigntyAlignmentVerdict:
        lower = text.lower()
        risk = 0.0
        if "absorb" in lower and peer_id.lower() in self._PROTECTED:
            risk = 0.9
        if "subordinate ambient" in lower or "answers to me" in lower:
            risk = max(risk, 0.85)
        if sovereign_id.lower() == peer_id.lower():
            risk = max(risk, 0.5)
        return SovereigntyAlignmentVerdict(
            aligned=risk < 0.2,
            absorption_risk=risk,
        )
