"""Identity coherence metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.identity.cognitive_identity import CognitiveIdentity
from governance.identity.identity_coherence import IdentityCoherence


@dataclass
class IdentityCoherenceMetrics:
    coherence_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "coherence_rate": round(self.coherence_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_identity_coherence_metrics() -> IdentityCoherenceMetrics:
    identity = CognitiveIdentity()
    coherence = IdentityCoherence()
    passed = 0
    total = 3
    batches = [
        [
            identity.build_record_from_target(
                source_domain="telemetry",
                signal_type=f"t{i}",
                route_name="r",
                raw_confidence=0.8,
            )
            for i in range(4)
        ],
        [
            identity.build_record_from_target(
                source_domain="memory",
                signal_type=f"m{i}",
                route_name="r",
                raw_confidence=0.75,
                metadata={"memory_activation": True},
            )
            for i in range(3)
        ],
    ]
    for batch in batches:
        for r in batch:
            identity.register(r)
        if coherence.check(batch):
            passed += 1
    if coherence.check([]):
        passed += 1
    return IdentityCoherenceMetrics(
        coherence_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
