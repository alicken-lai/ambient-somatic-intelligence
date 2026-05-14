"""Ontology Health Score — single metric for Ambient OS cognitive health."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .ontology_metrics import MetricResult, OntologyMetrics


class HealthClassification(Enum):
    """Overall ontology health classification."""

    STABLE = "stable"  # >= 0.90
    USABLE = "usable"  # >= 0.75
    EXPERIMENTAL = "experimental"  # >= 0.50
    UNSTABLE = "unstable"  # < 0.50


@dataclass
class HealthReport:
    """Result of a full health score computation."""

    score: float  # 0.0-1.0
    classification: HealthClassification
    metrics: list[MetricResult]
    timestamp: datetime
    details: str  # human-readable report
    passing: bool  # True if score >= threshold
    threshold: float


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OntologyHealthScore:
    """Computes and reports the overall ontology health score.

    The score is a weighted average of seven independent metrics, each
    normalised to [0.0, 1.0].  The final score is classified into one
    of four bands and compared against a configurable release-gate
    threshold.
    """

    METRIC_WEIGHTS: dict[str, float] = {
        "instinct_formation_rate": 0.15,
        "promotion_precision": 0.20,
        "decay_correctness": 0.15,
        "verifier_integrity": 0.15,
        "false_positive_resistance": 0.15,
        "strategic_emergence": 0.10,
        "confidence_calibration": 0.10,
    }

    def __init__(self, threshold: float = 0.85) -> None:
        self._threshold = threshold
        self._metrics = OntologyMetrics()

    # ── Core computation ──────────────────────────────────────────────

    def compute(self, **metric_inputs: dict) -> HealthReport:
        """Compute overall health score from explicit metric inputs.

        Each keyword should match a ``measure_*`` parameter set.  Keys:

        - ``instinct_formation_rate``: dict with l1_count, l2_count
        - ``promotion_precision``: dict with promoted_count,
          total_candidates, successful_promotions
        - ``decay_correctness``: dict with decayed_entries,
          contradiction_entries
        - ``verifier_integrity``: dict with total_verifications,
          self_certifications_blocked, independent_verifications
        - ``false_positive_resistance``: dict with noise_episodes,
          false_promotions
        - ``strategic_emergence``: dict with l3_count, l4_count,
          l4_with_governance
        - ``confidence_calibration``: dict with confidence_updates
        """
        results: list[MetricResult] = []

        dispatch = {
            "instinct_formation_rate": self._metrics.measure_instinct_formation_rate,
            "promotion_precision": self._metrics.measure_promotion_precision,
            "decay_correctness": self._metrics.measure_decay_correctness,
            "verifier_integrity": self._metrics.measure_verifier_integrity,
            "false_positive_resistance": self._metrics.measure_false_positive_resistance,
            "strategic_emergence": self._metrics.measure_strategic_emergence,
            "confidence_calibration": self._metrics.measure_confidence_calibration,
        }

        for name, weight in self.METRIC_WEIGHTS.items():
            inputs = metric_inputs.get(name)
            if inputs is None:
                results.append(MetricResult(
                    name=name,
                    value=0.0,
                    raw_value=0.0,
                    weight=weight,
                    description=f"No data provided for {name}",
                    measured_at=_utc_now(),
                ))
                continue
            fn = dispatch[name]
            result = fn(**inputs)
            result.weight = weight
            results.append(result)

        score = sum(r.value * r.weight for r in results)
        classification = self.classify(score)

        report = HealthReport(
            score=score,
            classification=classification,
            metrics=results,
            timestamp=_utc_now(),
            details="",
            passing=score >= self._threshold,
            threshold=self._threshold,
        )
        report.details = self.generate_report(report)
        return report

    def compute_from_test_results(self, test_results: dict) -> HealthReport:
        """Compute health score from stress test results.

        *test_results* should contain flat keys that are mapped to the
        seven metric groups:

        - l1_count, l2_count
        - promoted_count, total_candidates, successful_promotions
        - decayed_entries, contradiction_entries
        - total_verifications, self_certs_blocked,
          independent_verifications
        - noise_episodes, false_promotions
        - l3_count, l4_count, l4_with_governance
        - confidence_updates
        """
        grouped: dict[str, dict] = {
            "instinct_formation_rate": {
                "l1_count": test_results.get("l1_count", 0),
                "l2_count": test_results.get("l2_count", 0),
            },
            "promotion_precision": {
                "promoted_count": test_results.get("promoted_count", 0),
                "total_candidates": test_results.get("total_candidates", 0),
                "successful_promotions": test_results.get("successful_promotions", 0),
            },
            "decay_correctness": {
                "decayed_entries": test_results.get("decayed_entries", []),
                "contradiction_entries": test_results.get("contradiction_entries", []),
            },
            "verifier_integrity": {
                "total_verifications": test_results.get("total_verifications", 0),
                "self_certifications_blocked": test_results.get("self_certs_blocked", 0),
                "independent_verifications": test_results.get("independent_verifications", 0),
            },
            "false_positive_resistance": {
                "noise_episodes": test_results.get("noise_episodes", 0),
                "false_promotions": test_results.get("false_promotions", 0),
            },
            "strategic_emergence": {
                "l3_count": test_results.get("l3_count", 0),
                "l4_count": test_results.get("l4_count", 0),
                "l4_with_governance": test_results.get("l4_with_governance", 0),
            },
            "confidence_calibration": {
                "confidence_updates": test_results.get("confidence_updates", []),
            },
        }
        return self.compute(**grouped)

    # ── Classification ────────────────────────────────────────────────

    def classify(self, score: float) -> HealthClassification:
        """Classify a numeric score into a health band."""
        if score >= 0.90:
            return HealthClassification.STABLE
        elif score >= 0.75:
            return HealthClassification.USABLE
        elif score >= 0.50:
            return HealthClassification.EXPERIMENTAL
        else:
            return HealthClassification.UNSTABLE

    # ── Reporting ─────────────────────────────────────────────────────

    def generate_report(self, health_report: HealthReport) -> str:
        """Generate human-readable markdown report."""
        lines: list[str] = [
            "# Ontology Health Report",
            "",
            f"**Score:** {health_report.score:.4f}",
            f"**Classification:** {health_report.classification.value}",
            f"**Threshold:** {health_report.threshold}",
            f"**Passing:** {'YES' if health_report.passing else 'NO'}",
            f"**Timestamp:** {health_report.timestamp.isoformat()}",
            "",
            "## Metric Breakdown",
            "",
            "| Metric | Value | Weight | Weighted |",
            "|--------|-------|--------|----------|",
        ]

        for m in health_report.metrics:
            weighted = m.value * m.weight
            lines.append(
                f"| {m.name} | {m.value:.4f} | {m.weight:.2f} | {weighted:.4f} |"
            )

        lines.extend([
            "",
            "## Details",
            "",
        ])
        for m in health_report.metrics:
            lines.append(f"- **{m.name}**: {m.description}")

        return "\n".join(lines)

    # ── Release gate ──────────────────────────────────────────────────

    def passes_release_gate(self, health_report: HealthReport) -> bool:
        """Check if score meets release gate threshold (default 0.85)."""
        return health_report.score >= self._threshold
