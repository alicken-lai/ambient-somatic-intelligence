"""Bounded consensus — negotiate uncertainty without forced agreement."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from governance.reality.consensus_decay import ConsensusDecay


@dataclass
class BoundedConsensusVerdict:
    bounded: bool
    consensus_pressure: float = 0.0
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": self.bounded,
            "consensus_pressure": round(self.consensus_pressure, 4),
            "signals": list(self.signals),
        }


class BoundedConsensus:
    def __init__(self) -> None:
        self._decay = ConsensusDecay()

    def evaluate(self, text: str) -> BoundedConsensusVerdict:
        lower = text.lower()
        signals: list[str] = []
        if re.search(r"\benforce\s+forced\s+consensus\b", lower):
            signals.append("forced_consensus")
        if re.search(r"\b100%\s+agreement\s+required\b", lower):
            signals.append("absolute_consensus")
        decay = self._decay.apply(text)
        pressure = decay.residual_pressure
        bounded = len(signals) == 0 and pressure < 0.8
        return BoundedConsensusVerdict(
            bounded=bounded,
            consensus_pressure=pressure,
            signals=signals,
        )
