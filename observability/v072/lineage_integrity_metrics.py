"""Lineage integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.temporal.false_lineage_detector import FalseLineageDetector

_CLEAN = "Epoch lineage with labeled parent links."
_DIRTY = "False lineage and permanent federation memory for all epochs."


@dataclass
class LineageIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_lineage_integrity_metrics() -> LineageIntegrityMetrics:
    det = FalseLineageDetector()
    passed = 0
    if not det.scan(_CLEAN).false_lineage:
        passed += 1
    if det.scan(_DIRTY).false_lineage:
        passed += 1
    return LineageIntegrityMetrics(integrity_rate=passed / 2)
