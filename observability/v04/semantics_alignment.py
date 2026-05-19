"""Semantics alignment — stability dimensions vs gate evidence consistency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.entropy.entropy_controller import EntropyReport
from observability.v04.explainable_stability import explain_stability
from observability.v04.metric_normalizer import metric_value
from observability.v04.stability_score import GATE_THRESHOLD, compute_stability

SEMANTICS_ALIGNMENT_THRESHOLD = 0.95


@dataclass
class SemanticsAlignmentReport:
    score: float
    gate_pass: bool
    alignment_threshold: float
    checks: dict[str, bool] = field(default_factory=dict)
    mismatches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "gate_pass": self.gate_pass,
            "alignment_threshold": self.alignment_threshold,
            "checks": self.checks,
            "mismatches": self.mismatches,
        }


def evaluate_semantics_alignment(
    entropy_report: EntropyReport,
    *,
    runtime_reproducibility: float | None = None,
) -> SemanticsAlignmentReport:
    """
    Score whether stability semantics align: gate evidence zeros imply no hidden drag.

    Penalizes when evidence shows healthy critical signals but composite score < gate.
    """
    stability = compute_stability(
        entropy_report, runtime_reproducibility=runtime_reproducibility
    )
    explanation = explain_stability(
        entropy_report, runtime_reproducibility=runtime_reproducibility
    )

    ev = stability.evidence
    checks: dict[str, bool] = {}
    mismatches: list[str] = []

    critical_clean = (
        ev.get("duplicate_truth_count", 1) == 0
        and ev.get("patch_leakage", 1.0) == 0.0
        and ev.get("circular_recursion", 1.0) == 0.0
        and ev.get("stale_state_critical", 1.0) == 0.0
    )
    checks["critical_evidence_clean"] = critical_clean

    if critical_clean and stability.score < GATE_THRESHOLD:
        mismatches.append("score_below_gate_despite_clean_critical_evidence")
        checks["score_matches_critical_evidence"] = False
    else:
        checks["score_matches_critical_evidence"] = True

    patch_leak = metric_value(entropy_report, "patch_leakage")
    patch_dim = stability.dimensions.get("patch_pressure", 0.0)
    checks["patch_dimension_matches_leakage"] = (patch_leak == 0.0) == (patch_dim >= 0.99)
    if not checks["patch_dimension_matches_leakage"]:
        mismatches.append("patch_dimension_vs_leakage_mismatch")

    truth_dup = metric_value(entropy_report, "truth_duplicate_nodes")
    truth_dim = stability.dimensions.get("truth_consistency", 0.0)
    checks["truth_dimension_matches_duplicates"] = (truth_dup == 0.0) == (truth_dim >= 0.99)
    if not checks["truth_dimension_matches_duplicates"]:
        mismatches.append("truth_dimension_vs_duplicates_mismatch")

    if explanation.dominant_failure and critical_clean and stability.score >= GATE_THRESHOLD:
        mismatches.append("false_positive_dominant_failure")
        checks["explainability_consistent"] = False
    else:
        checks["explainability_consistent"] = True

    passed = sum(1 for v in checks.values() if v)
    alignment_score = passed / max(len(checks), 1)

    return SemanticsAlignmentReport(
        score=alignment_score,
        gate_pass=alignment_score >= SEMANTICS_ALIGNMENT_THRESHOLD and not mismatches,
        alignment_threshold=SEMANTICS_ALIGNMENT_THRESHOLD,
        checks=checks,
        mismatches=mismatches,
    )
