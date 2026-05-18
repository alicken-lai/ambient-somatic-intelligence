"""v0.4.3 isolation score — evidence-weighted execution authority composite."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.isolation.callback_guard import CallbackGuard
from kernel.isolation.execution_scope import ExecutionScope
from kernel.isolation.root_resolver import RootResolver
from kernel.isolation.write_guard import WriteGuard
from observability.v04.authority_trace import AuthorityTrace


class IsolationClassification(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    DEGRADED = "degraded"
    CRITICAL = "critical"


DIMENSION_WEIGHTS: dict[str, float] = {
    "writes_with_context": 0.20,
    "blocked_violations": 0.15,
    "sandbox_containment": 0.15,
    "callback_containment": 0.15,
    "root_ambiguity": 0.15,
    "rollback_coverage": 0.12,
    "cross_context_attempts": 0.08,
}

GATE_THRESHOLD = 0.85


@dataclass
class IsolationMetrics:
    total_writes: int = 0
    writes_with_context: int = 0
    blocked_violations: int = 0
    sandbox_leaks: int = 0
    callback_unregistered: int = 0
    callback_contained: int = 0
    root_ambiguity_events: int = 0
    rollback_missing_high_risk: int = 0
    cross_context_attempts: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total_writes": self.total_writes,
            "writes_with_context": self.writes_with_context,
            "blocked_violations": self.blocked_violations,
            "sandbox_leaks": self.sandbox_leaks,
            "callback_unregistered": self.callback_unregistered,
            "callback_contained": self.callback_contained,
            "root_ambiguity_events": self.root_ambiguity_events,
            "rollback_missing_high_risk": self.rollback_missing_high_risk,
            "cross_context_attempts": self.cross_context_attempts,
        }


@dataclass
class IsolationReport:
    score: float
    classification: IsolationClassification
    dimensions: dict[str, float] = field(default_factory=dict)
    gate_pass: bool = False
    metrics: IsolationMetrics = field(default_factory=IsolationMetrics)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "classification": self.classification.value,
            "gate_pass": self.gate_pass,
            "gate_threshold": GATE_THRESHOLD,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "metrics": self.metrics.to_dict(),
            "evidence": self.evidence,
        }


def compute_isolation(metrics: IsolationMetrics) -> IsolationReport:
    """Derive isolation score from observability metrics."""

    if metrics.total_writes == 0:
        write_ratio = 1.0
    else:
        write_ratio = metrics.writes_with_context / metrics.total_writes

    violation_pressure = min(1.0, metrics.blocked_violations * 0.05)
    sandbox_pressure = min(1.0, metrics.sandbox_leaks * 0.25)
    callback_total = metrics.callback_contained + metrics.callback_unregistered
    if callback_total == 0:
        callback_ratio = 1.0
    else:
        callback_ratio = metrics.callback_contained / callback_total
    root_pressure = min(1.0, metrics.root_ambiguity_events * 0.2)
    rollback_pressure = min(1.0, metrics.rollback_missing_high_risk * 0.3)
    cross_pressure = min(1.0, metrics.cross_context_attempts * 0.15)

    dimensions = {
        "writes_with_context": max(0.0, min(1.0, write_ratio)),
        "blocked_violations": max(0.0, 1.0 - violation_pressure),
        "sandbox_containment": max(0.0, 1.0 - sandbox_pressure),
        "callback_containment": max(0.0, min(1.0, callback_ratio)),
        "root_ambiguity": max(0.0, 1.0 - root_pressure),
        "rollback_coverage": max(0.0, 1.0 - rollback_pressure),
        "cross_context_attempts": max(0.0, 1.0 - cross_pressure),
    }

    score = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    score = max(0.0, min(1.0, score))

    if score >= GATE_THRESHOLD:
        classification = IsolationClassification.EXCELLENT
    elif score >= 0.70:
        classification = IsolationClassification.GOOD
    elif score >= 0.50:
        classification = IsolationClassification.DEGRADED
    else:
        classification = IsolationClassification.CRITICAL

    gate_pass = (
        score >= GATE_THRESHOLD
        and metrics.sandbox_leaks == 0
        and metrics.cross_context_attempts == 0
        and metrics.rollback_missing_high_risk == 0
    )

    return IsolationReport(
        score=score,
        classification=classification,
        dimensions=dimensions,
        gate_pass=gate_pass,
        metrics=metrics,
        evidence={
            "write_context_ratio": round(write_ratio, 4),
            "violation_count": metrics.blocked_violations,
        },
    )


def evaluate_isolation(
    *,
    write_guard: WriteGuard | None = None,
    callback_guard: CallbackGuard | None = None,
    scope: ExecutionScope | None = None,
    root_resolver: RootResolver | None = None,
    trace: AuthorityTrace | None = None,
) -> IsolationReport:
    """Convenience: gather metrics from live guards and compute score."""
    wg = write_guard or WriteGuard()
    cg = callback_guard or CallbackGuard()
    sc = scope or wg.scope
    rr = root_resolver or RootResolver()

    from kernel.isolation.execution_context import ExecutionContext, Permission
    from kernel.isolation.execution_scope import ScopeType
    from kernel.isolation.rollback_plan import RollbackPlan, RollbackType

    probe = ExecutionContext.create(
        caller_id="isolation-probe",
        scope=ScopeType.READ_ONLY.value,
        permissions={Permission.READ},
        rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
    )
    rr.bind_context(probe)
    root_resolved = rr.stats()["global_root"] is not None

    metrics = IsolationMetrics(
        total_writes=max(1, wg.stats()["allowed_writes"] + len(wg.violations)),
        writes_with_context=wg.stats()["allowed_writes"],
        blocked_violations=len(wg.violations),
        callback_contained=cg.stats()["contained_invocations"],
        callback_unregistered=max(0, len(cg._registry) - cg.stats()["contained_invocations"]),
        root_ambiguity_events=0 if root_resolved else 1,
        cross_context_attempts=len(sc.violations),
    )

    if trace:
        by_type = trace.by_type()
        metrics.sandbox_leaks = by_type.get("sandbox_leak", 0)
        metrics.rollback_missing_high_risk = by_type.get("rollback_missing", 0)

    return compute_isolation(metrics)
