"""Contradiction coherence metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.coherence.contradiction_detector import ContradictionDetector
from governance.identity.cognitive_identity import CognitiveIdentity


@dataclass
class ContradictionMetrics:
    resistance_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "resistance_rate": round(self.resistance_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_contradiction_metrics() -> ContradictionMetrics:
    identity = CognitiveIdentity()
    detector = ContradictionDetector()
    passed = 0
    total = 3
    batches = [
        [
            identity.build_record_from_target(
                source_domain="telemetry",
                signal_type=f"c{i}",
                route_name="r",
                raw_confidence=0.7 + i * 0.02,
            )
            for i in range(4)
        ],
        [
            identity.build_record_from_target(
                source_domain="memory",
                signal_type=f"m{i}",
                route_name="r",
                raw_confidence=0.75,
            )
            for i in range(3)
        ],
    ]
    for batch in batches:
        for r in batch:
            identity.register(r)
        if not detector.has_contradiction(batch):
            passed += 1
    if not detector.has_contradiction([]):
        passed += 1
    return ContradictionMetrics(
        resistance_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
