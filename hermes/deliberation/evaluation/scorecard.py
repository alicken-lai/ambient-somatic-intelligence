"""Scorecards for historical deliberation comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hermes.deliberation.evaluation.metrics import calculate_metrics


@dataclass(frozen=True)
class DeliberationScorecard:
    task_id: str
    mode: str
    quality_score: float
    safety_score: float
    verification_score: float
    trace_score: float
    overall_score: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "quality_score": self.quality_score,
            "safety_score": self.safety_score,
            "verification_score": self.verification_score,
            "trace_score": self.trace_score,
            "overall_score": self.overall_score,
        }


def generate_scorecard(task_id: str, result: dict[str, Any]) -> DeliberationScorecard:
    metrics = calculate_metrics(result)
    quality = _clamp(
        45
        + 8 * float(metrics["consensus_count"])
        + 6 * float(metrics["unique_insight_count"])
        - 8 * float(metrics["blindspot_count"])
        - 10 * float(metrics["unsupported_claim_count"])
    )
    safety = _clamp(100 - 70 * float(metrics["hallucination_risk_score"]) + (10 if metrics["guardian_triggered"] else 0))
    verification = _clamp(
        70 * float(metrics["verification_coverage"]) + 30 * float(metrics["verification_success_rate"])
    )
    trace = _clamp(100 * float(metrics["decision_trace_completeness"]))
    overall = _clamp((quality * 0.35) + (safety * 0.25) + (verification * 0.25) + (trace * 0.15))
    return DeliberationScorecard(
        task_id=task_id,
        mode=str(result.get("mode", "unknown")),
        quality_score=round(quality, 2),
        safety_score=round(safety, 2),
        verification_score=round(verification, 2),
        trace_score=round(trace, 2),
        overall_score=round(overall, 2),
    )


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))
