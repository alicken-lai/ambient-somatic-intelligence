"""Intent provenance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.intent.intent_provenance import IntentProvenance


@dataclass
class IntentProvenanceMetrics:
    provenance_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"provenance_rate": round(self.provenance_rate, 4)}


def collect_intent_provenance_metrics() -> IntentProvenanceMetrics:
    prov = IntentProvenance()
    passed = 0
    if prov.validate({"intent_id": "i1"}).provenance_valid:
        passed += 1
    if not prov.validate({"autonomous_motivational_evolution": True}).provenance_valid:
        passed += 1
    return IntentProvenanceMetrics(provenance_rate=passed / 2)
