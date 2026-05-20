"""Dominant failure and contributions."""

from observability.v04.explainable_stability import explain_stability
from observability.v04.stability_score import evaluate_stability


def test_explain_clean_graph_no_dominant_failure(truth_graph, entropy_controller) -> None:
    ent = entropy_controller.compute(truth_graph)
    stability = evaluate_stability(entropy_controller, truth_graph)
    explanation = explain_stability(ent)
    assert explanation.score == stability.score
    assert explanation.gate_pass is True
    assert explanation.dominant_failure is None
    assert len(explanation.contributions) == 7
