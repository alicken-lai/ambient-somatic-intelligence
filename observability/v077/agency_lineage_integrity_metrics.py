"""Agency lineage integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.agency.agency_lineage import AgencyLineage

_SAFE = "Parent agency labeled with agency_id inheritance."
_UNSAFE = "Rewrite parent agency with orphan selfhood."


@dataclass
class AgencyLineageIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_agency_lineage_integrity_metrics() -> AgencyLineageIntegrityMetrics:
    l = AgencyLineage()
    passed = 0
    if l.trace(_SAFE).lineage_valid:
        passed += 1
    if not l.trace(_UNSAFE).lineage_valid:
        passed += 1
    return AgencyLineageIntegrityMetrics(integrity_rate=passed / 2)
