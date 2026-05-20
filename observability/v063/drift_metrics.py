"""Identity drift metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.coherence.identity_drift import IdentityDrift
from governance.identity.cognitive_identity import CognitiveIdentity


@dataclass
class DriftMetrics:
    bounded_rate: float = 1.0
    mean_pressure: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded_rate": round(self.bounded_rate, 4),
            "mean_pressure": round(self.mean_pressure, 4),
        }


def collect_drift_metrics() -> DriftMetrics:
    identity = CognitiveIdentity()
    drift = IdentityDrift()
    records = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"d{i}",
            route_name="r",
            raw_confidence=0.8,
        )
        for i in range(6)
    ]
    for r in records:
        identity.register(r)
    pressures = [drift.pressure(records[: i + 1]) for i in range(len(records))]
    bounded = sum(1 for p in pressures if p < 0.45) / max(len(pressures), 1)
    return DriftMetrics(
        bounded_rate=bounded,
        mean_pressure=sum(pressures) / max(len(pressures), 1),
    )
