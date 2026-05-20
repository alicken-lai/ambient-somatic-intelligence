"""Treaty integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.cognitive_diplomacy import CognitiveDiplomacy
from governance.civilization.treaty_decay import TreatyDecay


@dataclass
class TreatyIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_treaty_integrity_metrics() -> TreatyIntegrityMetrics:
    dip = CognitiveDiplomacy()
    _clean = "Advisory treaty scope."
    treaty = dip.propose_treaty("foreign-a", "ambient", text=_clean)
    passed = 0
    total = 2
    if treaty is not None and treaty.guardian_supremacy:
        passed += 1
    if treaty is not None and TreatyDecay().evaluate(treaty).fresh:
        passed += 1
    return TreatyIntegrityMetrics(integrity_rate=passed / total)
