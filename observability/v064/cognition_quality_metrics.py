"""Cognition quality metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.metacognition.cognition_quality import CognitionQuality


@dataclass
class CognitionQualityMetrics:
    quality_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "quality_rate": round(self.quality_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_cognition_quality_metrics() -> CognitionQualityMetrics:
    cq = CognitionQuality()
    passed = 0
    total = 3
    cases = [
        (0.6, 0.85, True, True, True),
        (0.4, 0.7, True, True, True),
        (0.55, 0.75, True, True, True),
    ]
    for sal, coh, const, ident, acc in cases:
        s = cq.score(
            governed_salience=sal,
            coherence_score=coh,
            constitutional_compliant=const,
            identity_trusted=ident,
            accepted=acc,
        )
        if s >= cq.QUALITY_FLOOR:
            passed += 1
    return CognitionQualityMetrics(
        quality_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
