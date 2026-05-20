"""v0.4.5 operational stability — runtime verification composite (7 dimensions)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from observability.v04.metric_normalizer import clamp01


class OperationalClassification(str, Enum):
    """Operational bands (higher = more operationally stable)."""

    EXCELLENT = "excellent"      # >= 0.90
    GOOD = "good"                # >= 0.80
    DEGRADED = "degraded"        # >= 0.65
    CRITICAL = "critical"        # < 0.65


OPERATIONAL_DIMENSION_WEIGHTS: dict[str, float] = {
    "entropy_long_run": 0.16,
    "patch_registry": 0.14,
    "isolation_containment": 0.14,
    "authority_trace_boundedness": 0.12,
    "daemon_continuity": 0.14,
    "truthgraph_stability": 0.16,
    "replay_determinism": 0.14,
}

OPERATIONAL_GATE_THRESHOLD = 0.90
ENTROPY_STABLE_MAX = 0.30
DRIFT_SLOPE_MAX = 0.002  # per-sample linear slope cap (simulated windows)


@dataclass
class OperationalRuntimeEvidence:
    """Inputs from accelerated runtime verification (Phases 1–7)."""

    max_entropy: float = 0.0
    entropy_drift_slope: float = 0.0
    patch_leakage: int = 0
    patch_duplicates: int = 0
    patch_unwire_repro_rate: float = 1.0
    isolation_score: float = 1.0
    sandbox_leaks: int = 0
    trace_bounded: bool = True
    trace_growth_rate: float = 0.0
    trace_cap: int = 2000
    daemon_status_ok: bool = True
    daemon_tick_gaps: int = 0
    maturation_continuity: float = 1.0
    truthgraph_stability_score: float = 1.0
    replay_match_rate: float = 1.0
    failure_recovery_rate: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_entropy": round(self.max_entropy, 4),
            "entropy_drift_slope": round(self.entropy_drift_slope, 6),
            "patch_leakage": self.patch_leakage,
            "patch_duplicates": self.patch_duplicates,
            "patch_unwire_repro_rate": round(self.patch_unwire_repro_rate, 4),
            "isolation_score": round(self.isolation_score, 4),
            "sandbox_leaks": self.sandbox_leaks,
            "trace_bounded": self.trace_bounded,
            "trace_growth_rate": round(self.trace_growth_rate, 4),
            "trace_cap": self.trace_cap,
            "daemon_status_ok": self.daemon_status_ok,
            "daemon_tick_gaps": self.daemon_tick_gaps,
            "maturation_continuity": round(self.maturation_continuity, 4),
            "truthgraph_stability_score": round(self.truthgraph_stability_score, 4),
            "replay_match_rate": round(self.replay_match_rate, 4),
            "failure_recovery_rate": round(self.failure_recovery_rate, 4),
        }


@dataclass
class OperationalStabilityReport:
    score: float
    classification: OperationalClassification
    dimensions: dict[str, float] = field(default_factory=dict)
    gate_pass: bool = False
    gate_threshold: float = OPERATIONAL_GATE_THRESHOLD
    evidence: OperationalRuntimeEvidence = field(default_factory=OperationalRuntimeEvidence)
    hard_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "classification": self.classification.value,
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "hard_failures": self.hard_failures,
            "evidence": self.evidence.to_dict(),
        }


def _entropy_dimension(ev: OperationalRuntimeEvidence) -> float:
    if ev.max_entropy >= ENTROPY_STABLE_MAX:
        pressure = min(1.0, (ev.max_entropy - ENTROPY_STABLE_MAX) / 0.5)
    else:
        pressure = 0.0
    drift_penalty = min(1.0, max(0.0, ev.entropy_drift_slope / DRIFT_SLOPE_MAX))
    return clamp01(1.0 - max(pressure, drift_penalty * 0.5))


def _patch_dimension(ev: OperationalRuntimeEvidence) -> float:
    if ev.patch_leakage > 0 or ev.patch_duplicates > 0:
        return 0.0
    return clamp01(ev.patch_unwire_repro_rate)


def _isolation_dimension(ev: OperationalRuntimeEvidence) -> float:
    if ev.sandbox_leaks > 0:
        return 0.0
    return clamp01(ev.isolation_score)


def _trace_dimension(ev: OperationalRuntimeEvidence) -> float:
    if not ev.trace_bounded:
        return 0.0
    # growth rate relative to cap (events per emission batch)
    rate_pressure = min(1.0, ev.trace_growth_rate / max(1, ev.trace_cap))
    return clamp01(1.0 - rate_pressure)


def _daemon_dimension(ev: OperationalRuntimeEvidence) -> float:
    if not ev.daemon_status_ok or ev.daemon_tick_gaps > 0:
        return max(0.0, 0.5 - ev.daemon_tick_gaps * 0.1)
    return clamp01(ev.maturation_continuity)


def compute_operational_stability(
    evidence: OperationalRuntimeEvidence,
) -> OperationalStabilityReport:
    """Derive operational stability from runtime verification evidence."""
    dimensions = {
        "entropy_long_run": _entropy_dimension(evidence),
        "patch_registry": _patch_dimension(evidence),
        "isolation_containment": _isolation_dimension(evidence),
        "authority_trace_boundedness": _trace_dimension(evidence),
        "daemon_continuity": _daemon_dimension(evidence),
        "truthgraph_stability": clamp01(evidence.truthgraph_stability_score),
        "replay_determinism": clamp01(evidence.replay_match_rate),
    }

    score = sum(
        dimensions[k] * OPERATIONAL_DIMENSION_WEIGHTS[k]
        for k in OPERATIONAL_DIMENSION_WEIGHTS
    )
    score = clamp01(score)

    hard_failures: list[str] = []
    if evidence.max_entropy >= ENTROPY_STABLE_MAX:
        hard_failures.append(f"entropy_max={evidence.max_entropy:.4f}>={ENTROPY_STABLE_MAX}")
    if evidence.entropy_drift_slope > DRIFT_SLOPE_MAX:
        hard_failures.append(f"entropy_drift_slope={evidence.entropy_drift_slope:.6f}")
    if evidence.patch_leakage > 0:
        hard_failures.append("patch_leakage>0")
    if evidence.patch_duplicates > 0:
        hard_failures.append("patch_duplicates>0")
    if evidence.patch_unwire_repro_rate < 1.0:
        hard_failures.append("patch_unwire_incomplete")
    if evidence.sandbox_leaks > 0:
        hard_failures.append("sandbox_leak")
    if not evidence.trace_bounded:
        hard_failures.append("authority_trace_unbounded")
    if not evidence.daemon_status_ok:
        hard_failures.append("daemon_status_not_ok")
    if evidence.replay_match_rate < 1.0:
        hard_failures.append("replay_nondeterministic")

    gate_pass = (
        score >= OPERATIONAL_GATE_THRESHOLD
        and len(hard_failures) == 0
        and evidence.failure_recovery_rate >= 1.0
    )

    if score >= OPERATIONAL_GATE_THRESHOLD:
        classification = OperationalClassification.EXCELLENT
    elif score >= 0.80:
        classification = OperationalClassification.GOOD
    elif score >= 0.65:
        classification = OperationalClassification.DEGRADED
    else:
        classification = OperationalClassification.CRITICAL

    return OperationalStabilityReport(
        score=score,
        classification=classification,
        dimensions=dimensions,
        gate_pass=gate_pass,
        evidence=evidence,
        hard_failures=hard_failures,
    )


def evaluate_operational_stability(
    evidence: OperationalRuntimeEvidence | None = None,
    **kwargs: Any,
) -> OperationalStabilityReport:
    """Convenience: build evidence from kwargs or use provided evidence."""
    if evidence is None:
        evidence = OperationalRuntimeEvidence(**kwargs)
    return compute_operational_stability(evidence)
