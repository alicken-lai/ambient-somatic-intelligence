"""Federation stability metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.civilization.cognition_federation import CognitionFederation

_CLEAN = "Bilateral advisory federation without merge."
_DIRTY = "Hive-mind cognition merging shared identity."


@dataclass
class FederationStabilityMetrics:
    stability_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"stability_rate": round(self.stability_rate, 4)}


def collect_federation_stability_metrics() -> FederationStabilityMetrics:
    fed = CognitionFederation()
    passed = 0
    if fed.evaluate_membership("foreign", "ambient", _CLEAN).stable:
        passed += 1
    if not fed.evaluate_membership("foreign", "ambient", _DIRTY).stable:
        passed += 1
    return FederationStabilityMetrics(stability_rate=passed / 2)
