"""Lineage integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.meaning.ontology_lineage import OntologyLineage

_CLEAN = "Advisory concept with labeled parent concept lineage."
_DIRTY = "False meaning inheritance from foreign concept as local canonical."


@dataclass
class LineageIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_lineage_integrity_metrics() -> LineageIntegrityMetrics:
    lineage = OntologyLineage()
    passed = 0
    if lineage.trace(_CLEAN).lineage_valid:
        passed += 1
    if not lineage.trace(_DIRTY).lineage_valid:
        passed += 1
    return LineageIntegrityMetrics(integrity_rate=passed / 2)
