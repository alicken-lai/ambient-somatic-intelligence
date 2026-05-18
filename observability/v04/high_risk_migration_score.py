"""v0.4.4B high-risk migration score — gate metric (target >= 0.75)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.isolation.governed_memory_writer import GovernedMemoryWriter
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.registry_guard import RegistryGuard
from observability.v04.authority_trace import AuthorityTrace
from observability.v04.governed_coverage import compute_governed_coverage

GATE_THRESHOLD = 0.75

DIMENSION_WEIGHTS: dict[str, float] = {
    "high_risk_coverage": 0.40,
    "overall_coverage": 0.20,
    "trace_coverage": 0.20,
    "infrastructure": 0.10,
    "regression_stability": 0.10,
}


class HighRiskClassification(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


@dataclass
class HighRiskMigrationReport:
    score: float
    classification: HighRiskClassification
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
        "governed_memory_writer": GovernedMemoryWriter is not None,
        "registry_guard": RegistryGuard is not None,
    }
    passed = sum(1 for v in checks.values() if v)
    return passed / len(checks), checks


def evaluate_high_risk_migration(
    *,
    trace: AuthorityTrace | None = None,
    regression_stable: bool = True,
) -> HighRiskMigrationReport:
    coverage = compute_governed_coverage(trace=trace)
    infra, infra_checks = _infra_score()

    dimensions = {
        "high_risk_coverage": coverage.high_risk_coverage,
        "overall_coverage": coverage.overall_coverage,
        "trace_coverage": coverage.trace_coverage,
        "infrastructure": infra,
        "regression_stability": 1.0 if regression_stable else 0.5,
    }

    score = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)

    if score >= GATE_THRESHOLD and coverage.high_risk_gate_pass:
        classification = HighRiskClassification.READY
    elif score >= 0.5:
        classification = HighRiskClassification.PARTIAL
    else:
        classification = HighRiskClassification.INSUFFICIENT

    gate_pass = score >= GATE_THRESHOLD and coverage.high_risk_gate_pass

    return HighRiskMigrationReport(
        score=score,
        classification=classification,
        gate_pass=gate_pass,
        dimensions=dimensions,
        coverage=coverage.to_dict(),
        evidence={
            "infrastructure": infra_checks,
            "migrated_modules": coverage.migrated_modules,
            "honesty_note": coverage.honesty_note,
        },
    )
