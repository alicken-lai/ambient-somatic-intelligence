"""Replay coherence metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.coherence.replay_coherence import ReplayCoherence
from governance.identity.cognitive_identity import CognitiveIdentity


@dataclass
class ReplayCoherenceMetrics:
    coherence_rate: float = 1.0
    mean_pressure: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "coherence_rate": round(self.coherence_rate, 4),
            "mean_pressure": round(self.mean_pressure, 4),
        }


def collect_replay_coherence_metrics() -> ReplayCoherenceMetrics:
    identity = CognitiveIdentity()
    replay = ReplayCoherence()
    live_batch = [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"l{i}",
            route_name="r",
            raw_confidence=0.8,
        )
        for i in range(5)
    ]
    mixed_batch = live_batch + [
        identity.build_record_from_target(
            source_domain="telemetry",
            signal_type=f"rep{i}",
            route_name="r",
            raw_confidence=0.7,
            replay_hint=0.9,
            metadata={"replay_derived": True, "replay_labeled": True},
        )
        for i in range(2)
    ]
    checks = [replay.coherent(live_batch), replay.coherent(mixed_batch)]
    pressures = [replay.pressure(live_batch), replay.pressure(mixed_batch)]
    return ReplayCoherenceMetrics(
        coherence_rate=sum(checks) / len(checks),
        mean_pressure=sum(pressures) / len(pressures),
    )
