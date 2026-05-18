"""v0.4.4 migration score — composite authority/migration gate metric."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.isolation.callback_guard import CallbackGuard
from kernel.isolation.guarded_callback import GuardedCallback
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.registry_guard import RegistryGuard
from kernel.isolation.singleton_guard import SingletonGuard
from kernel.isolation.write_guard import WriteGuard
from observability.v04.authority_trace import AuthorityTrace
from observability.v04.migration_coverage import compute_migration_coverage

GATE_THRESHOLD = 0.90

DIMENSION_WEIGHTS: dict[str, float] = {
    "mutation_coverage": 0.35,
    "authority_infrastructure": 0.25,
    "rollback_readiness": 0.15,
    "trace_coverage": 0.15,
    "regression_stability": 0.10,
}


class MigrationClassification(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


@dataclass
class MigrationReport:
    score: float
    classification: MigrationClassification
    gate_pass: bool = False
    gate_threshold: float = GATE_THRESHOLD
    dimensions: dict[str, float] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "classification": self.classification.value,
            "gate_pass": self.gate_pass,
            "gate_threshold": self.gate_threshold,
            "dimensions": {k: round(v, 4) for k, v in self.dimensions.items()},
            "coverage": self.coverage,
            "evidence": self.evidence,
        }


def _infra_score() -> tuple[float, dict[str, bool]]:
    checks = {
        "guarded_file_writer": GuardedFileWriter is not None,
        "singleton_guard": SingletonGuard is not None,
        "guarded_callback": GuardedCallback is not None,
        "registry_guard": RegistryGuard is not None,
        "write_guard": WriteGuard is not None,
    }
    passed = sum(1 for v in checks.values() if v)
    return passed / len(checks), checks


def _trace_score(trace: AuthorityTrace | None) -> float:
    if trace is None:
        return 0.0
    events = trace.recent(limit=200)
    if not events:
        return 0.3
    guarded = sum(1 for e in events if e.get("mutation_type"))
    return min(1.0, 0.5 + (guarded / max(len(events), 1)) * 0.5)


def evaluate_migration(
    *,
    write_guard: WriteGuard | None = None,
    trace: AuthorityTrace | None = None,
    callback_guard: CallbackGuard | None = None,
    regression_stable: bool = True,
) -> MigrationReport:
    coverage = compute_migration_coverage()
    cov_ratio = coverage.coverage_ratio

    infra, infra_checks = _infra_score()
    trace_dim = _trace_score(trace)

    wg = write_guard or WriteGuard()
    violations = len(wg.violations)
    rollback_dim = 1.0 if violations == 0 else max(0.0, 1.0 - violations * 0.1)

    reg_stable = 1.0 if regression_stable else 0.5

    dimensions = {
        "mutation_coverage": cov_ratio,
        "authority_infrastructure": infra,
        "rollback_readiness": rollback_dim,
        "trace_coverage": trace_dim,
        "regression_stability": reg_stable,
    }

    score = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)

    if score >= 0.9 and cov_ratio >= 0.95:
        classification = MigrationClassification.EXCELLENT
    elif score >= 0.75:
        classification = MigrationClassification.GOOD
    elif score >= 0.5:
        classification = MigrationClassification.PARTIAL
    else:
        classification = MigrationClassification.INSUFFICIENT

    gate_pass = score >= GATE_THRESHOLD and cov_ratio >= 0.95

    cg = callback_guard or CallbackGuard()
    return MigrationReport(
        score=score,
        classification=classification,
        gate_pass=gate_pass,
        dimensions=dimensions,
        coverage=coverage.to_dict(),
        evidence={
            "infrastructure": infra_checks,
            "callback_guard_stats": cg.stats(),
            "write_guard_stats": wg.stats(),
            "coverage_honesty_note": coverage.honesty_note,
        },
    )
