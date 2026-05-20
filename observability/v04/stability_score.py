"""v0.4 stability score — evidence-weighted composite from entropy observables."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.entropy.entropy_controller import EntropyController, EntropyReport
from kernel.truth.truth_graph import TruthGraph
from observability.v04.metric_normalizer import (
    clamp01,
    dimension_from_pressure,
    metric_value,
    pressure_max,
)


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

# Gate-aligned metric subsets (max pressure, not kind-mean — avoids dilution/double penalty).
_TRUTH_PRESSURE_METRICS = (
    "truth_duplicate_nodes",
    "truth_checksum_divergence",
    "truth_conflict_pressure",
)
_PATCH_PRESSURE_METRICS = ("patch_leakage", "patch_unwire_failure")
_MUTATION_PRESSURE_METRICS = (
    "mutation_rate",
    "mutation_hook_pressure",
    "mutation_denial_rate",
)


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


def _dimension_pressures(entropy_report: EntropyReport) -> dict[str, float]:
    """Per-dimension pressures (0=healthy) using gate-aligned metric subsets."""
    truth_pressure = pressure_max(entropy_report, *_TRUTH_PRESSURE_METRICS)
    patch_pressure = pressure_max(entropy_report, *_PATCH_PRESSURE_METRICS)
    mutation_pressure = pressure_max(entropy_report, *_MUTATION_PRESSURE_METRICS)
    orphan_pressure = metric_value(entropy_report, "orphan_pressure")
    circular_coupling = metric_value(entropy_report, "circular_coupling")
    stale_pressure = max(
        metric_value(entropy_report, "stale_state_critical"),
        metric_value(entropy_report, "stale_state_pressure"),
    )

    return {
        "truth_consistency": truth_pressure,
        "patch_pressure": patch_pressure,
        "mutation_pressure": mutation_pressure,
        "orphan_pressure": orphan_pressure,
        "circular_coupling": circular_coupling,
        "stale_state": stale_pressure,
    }


def compute_stability(
    entropy_report: EntropyReport,
    *,
    runtime_reproducibility: float | None = None,
) -> StabilityReport:
    """
    Derive stability score from entropy observables.

    Each dimension is 1.0 - pressure (clamped), weighted per DIMENSION_WEIGHTS.
    Pressures use max-of-gate-metrics (not kind-mean) to avoid false penalties on clean graphs.
    """
    pressures = _dimension_pressures(entropy_report)

    if runtime_reproducibility is None:
        runtime_reproducibility = dimension_from_pressure(
            pressures["patch_pressure"] + pressures["mutation_pressure"] * 0.3
        )

    dimensions = {
        name: dimension_from_pressure(pressures[name])
        for name in (
            "truth_consistency",
            "patch_pressure",
            "mutation_pressure",
            "orphan_pressure",
            "circular_coupling",
            "stale_state",
        )
    }
    dimensions["runtime_reproducibility"] = clamp01(runtime_reproducibility)

    score = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    score = clamp01(score)

    if score >= GATE_THRESHOLD:
        classification = StabilityClassification.EXCELLENT
    elif score >= 0.70:
        classification = StabilityClassification.GOOD
    elif score >= 0.50:
        classification = StabilityClassification.DEGRADED
    else:
        classification = StabilityClassification.CRITICAL

    duplicate_truth = metric_value(entropy_report, "truth_duplicate_nodes")
    patch_leak = metric_value(entropy_report, "patch_leakage")
    circular = metric_value(entropy_report, "circular_coupling")
    stale_critical = metric_value(entropy_report, "stale_state_critical")

    evidence = {
        "duplicate_truth_count": int(duplicate_truth > 0),
        "patch_leakage": patch_leak,
        "circular_recursion": circular,
        "stale_state_critical": stale_critical,
        "pressures": {k: round(v, 4) for k, v in pressures.items()},
    }

    return StabilityReport(
        score=score,
        classification=classification,
        dimensions=dimensions,
        entropy_score=entropy_report.score,
        gate_pass=score >= GATE_THRESHOLD
        and duplicate_truth == 0
        and patch_leak == 0
        and circular == 0
        and stale_critical == 0,
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
