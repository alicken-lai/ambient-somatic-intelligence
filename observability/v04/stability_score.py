"""v0.4 stability score — evidence-weighted composite from entropy observables."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.entropy.entropy_controller import EntropyController, EntropyReport
from kernel.entropy.entropy_metric import MetricKind
from kernel.truth.truth_graph import TruthGraph


class StabilityClassification(str, Enum):
    """Stability bands (higher score = more stable)."""

    EXCELLENT = "excellent"      # >= 0.85
    GOOD = "good"                # >= 0.70
    DEGRADED = "degraded"        # >= 0.50
    CRITICAL = "critical"        # < 0.50


# Evidence-based weights (sum = 1.0); aligned with v042 gate dimensions.
DIMENSION_WEIGHTS: dict[str, float] = {
    "truth_consistency": 0.22,
    "patch_pressure": 0.18,
    "mutation_pressure": 0.14,
    "orphan_pressure": 0.12,
    "circular_coupling": 0.14,
    "stale_state": 0.12,
    "runtime_reproducibility": 0.08,
}

GATE_THRESHOLD = 0.85


@dataclass
class StabilityReport:
    """Composite stability assessment (1.0 = fully stable)."""

    score: float
    classification: StabilityClassification
    dimensions: dict[str, float] = field(default_factory=dict)
    entropy_score: float = 0.0
    gate_pass: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "classification": self.classification.value,
            "gate_pass": self.gate_pass,
            "gate_threshold": GATE_THRESHOLD,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "entropy_score": round(self.entropy_score, 4),
            "evidence": self.evidence,
        }


def _metric_value(report: EntropyReport, name: str, default: float = 0.0) -> float:
    for metric in report.snapshot.metrics:
        if metric.name == name:
            return metric.value
    return default


def _kind_mean(report: EntropyReport, kind: MetricKind) -> float:
    metrics = report.snapshot.by_kind(kind)
    if not metrics:
        return 0.0
    return sum(m.value for m in metrics) / len(metrics)


def compute_stability(
    entropy_report: EntropyReport,
    *,
    runtime_reproducibility: float | None = None,
) -> StabilityReport:
    """
    Derive stability score from entropy observables.

    Each dimension is 1.0 - pressure (clamped), weighted per DIMENSION_WEIGHTS.
    """
    truth_pressure = max(
        _metric_value(entropy_report, "truth_duplicate_nodes"),
        _metric_value(entropy_report, "truth_checksum_divergence"),
        _kind_mean(entropy_report, MetricKind.DRIFT) * 0.5,
    )
    patch_pressure = max(
        _metric_value(entropy_report, "patch_leakage"),
        _kind_mean(entropy_report, MetricKind.PATCH),
    )
    mutation_pressure = _kind_mean(entropy_report, MetricKind.MUTATION)
    orphan_pressure = _metric_value(entropy_report, "orphan_pressure")
    circular_coupling = _metric_value(entropy_report, "circular_coupling")
    stale_pressure = max(
        _metric_value(entropy_report, "stale_state_critical"),
        _kind_mean(entropy_report, MetricKind.STALE),
    )

    if runtime_reproducibility is None:
        runtime_reproducibility = 1.0 - min(1.0, patch_pressure + mutation_pressure * 0.3)

    dimensions = {
        "truth_consistency": max(0.0, 1.0 - truth_pressure),
        "patch_pressure": max(0.0, 1.0 - patch_pressure),
        "mutation_pressure": max(0.0, 1.0 - mutation_pressure),
        "orphan_pressure": max(0.0, 1.0 - orphan_pressure),
        "circular_coupling": max(0.0, 1.0 - circular_coupling),
        "stale_state": max(0.0, 1.0 - stale_pressure),
        "runtime_reproducibility": max(0.0, min(1.0, runtime_reproducibility)),
    }

    score = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    score = max(0.0, min(1.0, score))

    if score >= GATE_THRESHOLD:
        classification = StabilityClassification.EXCELLENT
    elif score >= 0.70:
        classification = StabilityClassification.GOOD
    elif score >= 0.50:
        classification = StabilityClassification.DEGRADED
    else:
        classification = StabilityClassification.CRITICAL

    duplicate_truth = _metric_value(entropy_report, "truth_duplicate_nodes")
    patch_leak = _metric_value(entropy_report, "patch_leakage")

    evidence = {
        "duplicate_truth_count": int(duplicate_truth > 0),
        "patch_leakage": patch_leak,
        "circular_recursion": circular_coupling,
        "stale_state_critical": _metric_value(entropy_report, "stale_state_critical"),
    }

    return StabilityReport(
        score=score,
        classification=classification,
        dimensions=dimensions,
        entropy_score=entropy_report.score,
        gate_pass=score >= GATE_THRESHOLD
        and duplicate_truth == 0
        and patch_leak == 0
        and circular_coupling == 0
        and _metric_value(entropy_report, "stale_state_critical") == 0,
        evidence=evidence,
    )


def evaluate_stability(
    controller: EntropyController | None = None,
    truth_graph: TruthGraph | None = None,
    **kwargs: Any,
) -> StabilityReport:
    """Convenience: compute entropy then stability."""
    ctrl = controller or EntropyController()
    entropy = ctrl.compute(truth_graph, **kwargs)
    return compute_stability(entropy)
