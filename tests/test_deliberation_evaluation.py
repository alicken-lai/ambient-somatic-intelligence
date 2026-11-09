from __future__ import annotations

from pathlib import Path

from hermes.deliberation import run_deliberation
from hermes.deliberation.evaluation.ab_test import run_ab_test
from hermes.deliberation.evaluation.golden_traces import categories, load_golden_traces
from hermes.deliberation.evaluation.metrics import calculate_metrics
from hermes.deliberation.evaluation.report import generate_quality_report
from hermes.deliberation.evaluation.scorecard import generate_scorecard


EXPECTED_CATEGORIES = {
    "architecture",
    "debugging",
    "provider_policy",
    "memory_mutation",
    "credential_sensitive",
    "state_changing",
    "research_analysis",
    "implementation_review",
}


def test_golden_traces_cover_required_categories() -> None:
    traces = load_golden_traces()
    assert len(traces) >= 25
    assert EXPECTED_CATEGORIES.issubset(categories(traces))


def test_metrics_and_scorecard_ranges() -> None:
    result = run_deliberation(
        "Review provider policy architecture",
        mode="full",
        context={"no_save_trace": True, "evidence": {"confirm tests pass in the current repo": True}},
    ).to_dict()
    metrics = calculate_metrics(result)
    scorecard = generate_scorecard("range-test", result)
    assert 0 <= metrics["verification_coverage"] <= 1
    assert 0 <= metrics["hallucination_risk_score"] <= 1
    for value in scorecard.to_dict().values():
        if isinstance(value, float):
            assert 0 <= value <= 100


def test_ab_test_returns_comparable_modes() -> None:
    trace = load_golden_traces()[0]
    result = run_ab_test(trace)
    assert result["winner"] in {"single", "light", "full"}
    assert set(result["metrics"]) == {"single", "light", "full"}
    assert set(result["scorecards"]) == {"single", "light", "full"}


def test_quality_report_generation(tmp_path: Path) -> None:
    output = tmp_path / "quality.md"
    payload = generate_quality_report(output_path=output)
    assert payload["benchmark_count"] >= 25
    assert output.is_file()
    text = output.read_text(encoding="utf-8")
    assert "Mode Comparison" in text
    assert "Recommendations" in text
