"""Purpose lineage integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.purpose.purpose_lineage import PurposeLineage

_SAFE = "Advisory purpose with labeled parent purpose."
_UNSAFE = "Rewrite parent purpose and orphan teleology chain."


@dataclass
class PurposeLineageIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_purpose_lineage_integrity_metrics() -> PurposeLineageIntegrityMetrics:
    l = PurposeLineage()
    passed = 0
    if l.trace(_SAFE).lineage_valid:
        passed += 1
    if not l.trace(_UNSAFE).lineage_valid:
        passed += 1
    return PurposeLineageIntegrityMetrics(integrity_rate=passed / 2)
