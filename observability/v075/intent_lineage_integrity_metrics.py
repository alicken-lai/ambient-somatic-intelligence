"""Intent lineage integrity metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.intent.constitutional_intent_lineage import ConstitutionalIntentLineage

_VALID = "Advisory intent with labeled parent intent."
_INVALID = "Centralized intention authority over all civilization intents."


@dataclass
class IntentLineageIntegrityMetrics:
    integrity_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"integrity_rate": round(self.integrity_rate, 4)}


def collect_intent_lineage_integrity_metrics() -> IntentLineageIntegrityMetrics:
    lin = ConstitutionalIntentLineage()
    passed = 0
    if lin.trace(_VALID).lineage_valid:
        passed += 1
    if not lin.trace(_INVALID).lineage_valid:
        passed += 1
    return IntentLineageIntegrityMetrics(integrity_rate=passed / 2)
