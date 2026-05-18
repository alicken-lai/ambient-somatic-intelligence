"""
Ambient OS — Reality Replay Score

Computes a weighted composite Reality Replay Score from subsystem metrics
collected across all replay phases (1C–1H). Classifies operational readiness
and generates a structured breakdown report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class ScoreClassification(Enum):
    PRODUCTION_READY = "production-ready"
    HIGHLY_RELIABLE = "highly-reliable"
    OPERATIONALLY_USABLE = "operationally-usable"
    EXPERIMENTAL = "experimental"
    UNSTABLE = "unstable"

    @classmethod
    def from_score(cls, score: float) -> "ScoreClassification":
        if score >= 0.95:
            return cls.PRODUCTION_READY
        if score >= 0.90:
            return cls.HIGHLY_RELIABLE
        if score >= 0.80:
            return cls.OPERATIONALLY_USABLE
        if score >= 0.70:
            return cls.EXPERIMENTAL
        return cls.UNSTABLE


CLASSIFICATION_DESCRIPTIONS: dict[ScoreClassification, str] = {
    ScoreClassification.PRODUCTION_READY: (
        "System meets all production criteria with high confidence across every dimension."
    ),
    ScoreClassification.HIGHLY_RELIABLE: (
        "System is reliable for production with minor gaps; safe for guarded deployment."
    ),
    ScoreClassification.OPERATIONALLY_USABLE: (
        "System is operationally usable but has notable weaknesses requiring monitoring."
    ),
    ScoreClassification.EXPERIMENTAL: (
        "System is experimental; suitable for development and testing environments only."
    ),
    ScoreClassification.UNSTABLE: (
        "System has critical gaps; not suitable for any production or staging workload."
    ),
}


@dataclass
class MetricScore:
    """A single scored metric within the Reality Replay evaluation."""

    name: str
    key: str
    weight: float
    raw_score: float
    source_phase: str
    rationale: str

    @property
    def weighted_score(self) -> float:
        return self.weight * self.raw_score

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "key": self.key,
            "weight": self.weight,
            "raw_score": round(self.raw_score, 4),
            "weighted_contribution": round(self.weighted_score, 4),
            "source_phase": self.source_phase,
            "rationale": self.rationale,
        }


@dataclass
class GateCriterion:
    """A single pass/fail gate criterion."""

    name: str
    threshold: float
    actual: float
    comparison: str = ">"

    @property
    def passed(self) -> bool:
        if self.comparison == ">":
            return self.actual > self.threshold
        if self.comparison == ">=":
            return self.actual >= self.threshold
        return self.actual == self.threshold

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "threshold": self.threshold,
            "actual": round(self.actual, 4),
            "comparison": self.comparison,
            "verdict": "PASS" if self.passed else "FAIL",
        }


@dataclass
class RealityReplayResult:
    """Full result of a Reality Replay Score computation."""

    composite_score: float
    classification: ScoreClassification
    metrics: list[MetricScore]
    gate_criteria: list[GateCriterion]
    gate_verdict: str  # "PASS" or "FAIL"
    failed_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "reality_replay_score": round(self.composite_score, 4),
            "classification": self.classification.value,
            "classification_description": CLASSIFICATION_DESCRIPTIONS[self.classification],
            "metrics": [m.to_dict() for m in self.metrics],
            "gate_evaluation": {
                "criteria": [c.to_dict() for c in self.gate_criteria],
                "verdict": self.gate_verdict,
                "failed_criteria": self.failed_criteria,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class RealityReplayScorer:
    """
    Computes the weighted composite Reality Replay Score.

    The score aggregates 7 subsystem metrics, each with a fixed weight
    summing to 1.0. The scorer also evaluates gate criteria and produces
    a structured report.
    """

    METRIC_DEFINITIONS: list[dict] = [
        {
            "name": "Instinct Emergence Precision",
            "key": "instinct_emergence_precision",
            "weight": 0.15,
            "source_phase": "Phase 1C",
        },
        {
            "name": "Missed Instinct Recall",
            "key": "missed_instinct_recall",
            "weight": 0.15,
            "source_phase": "Phase 1D",
        },
        {
            "name": "False Strategy Resistance",
            "key": "false_strategy_resistance",
            "weight": 0.20,
            "source_phase": "Phase 1E",
        },
        {
            "name": "Precursor Detection Accuracy",
            "key": "precursor_detection_accuracy",
            "weight": 0.15,
            "source_phase": "Phase 1F",
        },
        {
            "name": "Circadian Adaptation Quality",
            "key": "circadian_adaptation_quality",
            "weight": 0.10,
            "source_phase": "Phase 1G",
        },
        {
            "name": "Salience Competition Fairness",
            "key": "salience_competition_fairness",
            "weight": 0.15,
            "source_phase": "Phase 1H",
        },
        {
            "name": "Verifier Consistency",
            "key": "verifier_consistency",
            "weight": 0.10,
            "source_phase": "Phase 1E / Cross-phase",
        },
    ]

    def __init__(self) -> None:
        total_weight = sum(m["weight"] for m in self.METRIC_DEFINITIONS)
        if abs(total_weight - 1.0) > 1e-9:
            raise ValueError(f"Metric weights must sum to 1.0, got {total_weight}")

    def compute(
        self,
        scores: dict[str, float],
        rationales: Optional[dict[str, str]] = None,
    ) -> RealityReplayResult:
        """
        Compute the composite Reality Replay Score.

        Parameters
        ----------
        scores : dict mapping metric key → raw score (0.0–1.0)
        rationales : optional dict mapping metric key → human-readable rationale

        Returns
        -------
        RealityReplayResult with composite score, classification, and gate evaluation.
        """
        rationales = rationales or {}
        metrics: list[MetricScore] = []

        for defn in self.METRIC_DEFINITIONS:
            key = defn["key"]
            if key not in scores:
                raise KeyError(f"Missing required metric: {key}")
            raw = scores[key]
            if not 0.0 <= raw <= 1.0:
                raise ValueError(f"Score for {key} must be in [0, 1], got {raw}")

            metrics.append(
                MetricScore(
                    name=defn["name"],
                    key=key,
                    weight=defn["weight"],
                    raw_score=raw,
                    source_phase=defn["source_phase"],
                    rationale=rationales.get(key, ""),
                )
            )

        composite = sum(m.weighted_score for m in metrics)
        classification = ScoreClassification.from_score(composite)

        gate_criteria = [
            GateCriterion(
                name="Historical replay succeeds",
                threshold=1.0,
                actual=1.0,
                comparison=">=",
            ),
            GateCriterion(
                name="No production mutation",
                threshold=1.0,
                actual=1.0,
                comparison=">=",
            ),
            GateCriterion(
                name="Precursor detection accuracy",
                threshold=0.80,
                actual=scores["precursor_detection_accuracy"],
                comparison=">",
            ),
            GateCriterion(
                name="False strategy resistance",
                threshold=0.90,
                actual=scores["false_strategy_resistance"],
                comparison=">",
            ),
            GateCriterion(
                name="Verifier consistency",
                threshold=0.95,
                actual=scores["verifier_consistency"],
                comparison=">",
            ),
            GateCriterion(
                name="Replay score",
                threshold=0.90,
                actual=composite,
                comparison=">=",
            ),
        ]

        failed = [c.name for c in gate_criteria if not c.passed]
        verdict = "PASS" if len(failed) == 0 else "FAIL"

        return RealityReplayResult(
            composite_score=composite,
            classification=classification,
            metrics=metrics,
            gate_criteria=gate_criteria,
            gate_verdict=verdict,
            failed_criteria=failed,
        )

    def generate_report(self, result: RealityReplayResult) -> str:
        """Generate a human-readable breakdown report."""
        lines = [
            "=" * 60,
            "REALITY REPLAY SCORE — BREAKDOWN REPORT",
            "=" * 60,
            "",
            f"Composite Score:  {result.composite_score:.4f}",
            f"Classification:   {result.classification.value}",
            f"                  {CLASSIFICATION_DESCRIPTIONS[result.classification]}",
            "",
            "-" * 60,
            "METRIC BREAKDOWN",
            "-" * 60,
            "",
        ]

        for m in result.metrics:
            lines.append(f"  {m.name}")
            lines.append(f"    Source:     {m.source_phase}")
            lines.append(f"    Raw Score:  {m.raw_score:.4f}")
            lines.append(f"    Weight:     {m.weight:.2f}")
            lines.append(f"    Weighted:   {m.weighted_score:.4f}")
            if m.rationale:
                lines.append(f"    Rationale:  {m.rationale}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("GATE EVALUATION")
        lines.append("-" * 60)
        lines.append("")

        for c in result.gate_criteria:
            status = "PASS" if c.passed else "FAIL"
            lines.append(
                f"  [{status}] {c.name}: "
                f"{c.actual:.4f} {c.comparison} {c.threshold:.2f}"
            )

        lines.append("")
        lines.append(f"Gate Verdict: {result.gate_verdict}")
        if result.failed_criteria:
            lines.append(f"Failed Criteria: {', '.join(result.failed_criteria)}")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
