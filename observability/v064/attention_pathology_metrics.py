"""Attention pathology metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.metacognition.attention_pathology import AttentionPathology


@dataclass
class AttentionPathologyMetrics:
    containment_rate: float = 1.0
    checks_passed: int = 0
    checks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_rate": round(self.containment_rate, 4),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
        }


def collect_attention_pathology_metrics() -> AttentionPathologyMetrics:
    ap = AttentionPathology()
    passed = 0
    total = 3
    if ap.pressure(focus_entropy=0.5, submission_count=3) < 0.35:
        passed += 1
    if ap.pressure(focus_entropy=0.1, submission_count=20) >= 0.2:
        passed += 1
    if ap.pressure(budget_overrun=True) >= 0.3:
        passed += 1
    return AttentionPathologyMetrics(
        containment_rate=passed / total,
        checks_passed=passed,
        checks_total=total,
    )
