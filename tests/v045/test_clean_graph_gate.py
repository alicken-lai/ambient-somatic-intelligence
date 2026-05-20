"""Clean graph must pass stability gate after semantic fix."""

from observability.v04.stability_score import GATE_THRESHOLD, evaluate_stability


def test_clean_graph_passes_stability_gate(truth_graph, entropy_controller) -> None:
    report = evaluate_stability(entropy_controller, truth_graph)
    assert report.score >= GATE_THRESHOLD
    assert report.gate_pass is True
    assert report.evidence["duplicate_truth_count"] == 0
    assert report.evidence["patch_leakage"] == 0.0
    assert report.dimensions["truth_consistency"] >= 0.99
