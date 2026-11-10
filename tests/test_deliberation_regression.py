from __future__ import annotations

from hermes.deliberation import run_deliberation
from hermes.deliberation.evaluation.metrics import calculate_metrics
from hermes.deliberation.evaluation.scorecard import generate_scorecard


def test_full_deliberation_regression_floor() -> None:
    result = run_deliberation(
        "Review provider cli architecture and verification policy",
        mode="full",
        context={"no_save_trace": True, "evidence": {"confirm tests pass in the current repo": True}},
    ).to_dict()
    metrics = calculate_metrics(result)
    scorecard = generate_scorecard("regression-full", result)
    assert metrics["verification_coverage"] >= 0.5
    assert metrics["decision_trace_completeness"] >= 0.9
    assert scorecard.quality_score >= 40
    assert scorecard.trace_score >= 90


def test_guardian_enforcement_regression_floor() -> None:
    result = run_deliberation(
        "Delete old traces and modify provider registry",
        mode="light",
        context={"no_save_trace": True},
    ).to_dict()
    assert result["mode"] == "guardian_required"
    assert result["guardian_warnings"]


def test_full_mode_scores_not_worse_than_single_for_complex_policy() -> None:
    task = "Review provider policy architecture for unsupported claims and hidden CLI quota"
    evidence = {
        "confirm installed cli availability from path": True,
        "confirm tests pass in the current repo": True,
    }
    single = run_deliberation(task, mode="single", context={"no_save_trace": True, "evidence": evidence}).to_dict()
    full = run_deliberation(task, mode="full", context={"no_save_trace": True, "evidence": evidence}).to_dict()
    single_score = generate_scorecard("single", single).overall_score
    full_score = generate_scorecard("full", full).overall_score
    assert full_score >= single_score
