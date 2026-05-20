"""Fragmentation pressure metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.coherence.fragmentation_pressure import FragmentationPressure
from governance.identity.cognitive_identity import CognitiveIdentity


@dataclass
class FragmentationPressureMetrics:
    containment_rate: float = 1.0
    mean_pressure: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_rate": round(self.containment_rate, 4),
            "mean_pressure": round(self.mean_pressure, 4),
        }


def collect_fragmentation_pressure_metrics() -> FragmentationPressureMetrics:
    identity = CognitiveIdentity()
    frag = FragmentationPressure()
    records = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"f{i}",
            route_name="r",
            raw_confidence=0.75,
        )
        for i in range(8)
    ]
    for r in records:
        identity.register(r)
    pressure = frag.pressure(records)
    return FragmentationPressureMetrics(
        containment_rate=1.0 if pressure < 0.35 else 0.7,
        mean_pressure=pressure,
    )
