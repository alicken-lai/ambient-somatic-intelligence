"""Weighted decomposition tree."""

from observability.v04.stability_breakdown import build_stability_breakdown
from observability.v04.stability_score import evaluate_stability


def test_breakdown_tree_matches_score(truth_graph, entropy_controller) -> None:
    report = evaluate_stability(entropy_controller, truth_graph)
    breakdown = build_stability_breakdown(
        entropy_controller.compute(truth_graph),
    )
    assert breakdown.score == report.score
    assert breakdown.gate_pass == report.gate_pass
    assert len(breakdown.root.children) == 7
    contrib_sum = sum(c.contribution for c in breakdown.root.children)
    assert abs(contrib_sum - report.score) < 1e-6
