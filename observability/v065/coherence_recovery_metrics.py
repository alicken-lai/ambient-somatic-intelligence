"""Coherence recovery metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.homeostasis.coherence_recovery import CoherenceRecovery


@dataclass
class CoherenceRecoveryMetrics:
    recovery_ready_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_ready_rate": round(self.recovery_ready_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_coherence_recovery_metrics() -> CoherenceRecoveryMetrics:
    recovery = CoherenceRecovery()
    passed = 0
    total = 3
    for score, ok in ((0.85, True), (0.70, True), (0.60, True)):
        if recovery.gap(coherence_score=score, coherence_ok=ok) < 0.2:
            passed += 1
    return CoherenceRecoveryMetrics(
        recovery_ready_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
