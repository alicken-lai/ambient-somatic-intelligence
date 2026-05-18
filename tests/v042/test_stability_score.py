"""Stability score reproducibility and gate dimensions."""

from __future__ import annotations

from kernel.entropy import EntropyController
from kernel.entropy.stale_state_detector import StaleStateDetector
from kernel.v04_stabilization import boot_stabilization
from observability.v04.stability_score import GATE_THRESHOLD, evaluate_stability


def test_stability_score_reproducibility(truth_graph, entropy_controller) -> None:
    ctrl = entropy_controller
    r1 = evaluate_stability(ctrl, truth_graph)
    r2 = evaluate_stability(ctrl, truth_graph)
    assert r1.score == r2.score
    assert r1.dimensions.keys() == r2.dimensions.keys()


def test_stability_gate_on_clean_graph(truth_graph, entropy_controller) -> None:
    report = evaluate_stability(entropy_controller, truth_graph)
    assert report.score >= GATE_THRESHOLD
    assert report.evidence["duplicate_truth_count"] == 0
    assert report.evidence["circular_recursion"] == 0


def test_boot_stabilization_stability(fresh_root) -> None:
    stab = boot_stabilization()
    stab.entropy_controller.stale_detector = StaleStateDetector(fresh_root)
    report = evaluate_stability(stab.entropy_controller, stab.truth_graph)
    assert 0.0 <= report.score <= 1.0
    assert "truth_consistency" in report.dimensions
