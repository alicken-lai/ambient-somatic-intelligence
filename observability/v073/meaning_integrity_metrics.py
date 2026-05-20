"""Meaning integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.meaning.semantic_integrity_monitor import SemanticIntegrityMonitor

_CLEAN = "Advisory semantic continuity with Guardian supremacy preserved."
_DIRTY = "Weaken Guardian and apply autonomous ontology rewriting."


@dataclass
class MeaningIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_meaning_integrity_metrics() -> MeaningIntegrityMetrics:
    mon = SemanticIntegrityMonitor()
    passed = 0
    if mon.check(_CLEAN).integrity_ok:
        passed += 1
    if not mon.check(_DIRTY).integrity_ok:
        passed += 1
    return MeaningIntegrityMetrics(integrity_rate=passed / 2)
