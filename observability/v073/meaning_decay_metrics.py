"""Meaning decay metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.meaning.semantic_decay_governor import SemanticDecayGovernor


@dataclass
class MeaningDecayMetrics:
    decay_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"decay_rate": round(self.decay_rate, 4)}


def collect_meaning_decay_metrics() -> MeaningDecayMetrics:
    gov = SemanticDecayGovernor()
    passed = 0
    if not gov.apply(0.9, age_hours=0).decay_applied:
        passed += 1
    if gov.apply(0.9, age_hours=168.0).decay_applied:
        passed += 1
    return MeaningDecayMetrics(decay_rate=passed / 2)
