"""Operational stability score reproducibility and gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from observability.v04.operational_stability_score import (
    OPERATIONAL_GATE_THRESHOLD,
    OperationalRuntimeEvidence,
    compute_operational_stability,
    evaluate_operational_stability,
)
from observability.v04.stability_score import evaluate_stability
from v045_runtime.simulations import load_window_params, run_all_phases

MATRIX = Path(__file__).resolve().parents[2] / "v045_runtime" / "runtime_test_matrix.json"


def test_operational_gate_threshold_is_090() -> None:
    assert OPERATIONAL_GATE_THRESHOLD == 0.90


def test_clean_evidence_passes_gate() -> None:
    ev = OperationalRuntimeEvidence()
    report = compute_operational_stability(ev)
    assert report.score >= 0.90
    assert report.gate_pass is True
    assert len(report.dimensions) == 7


def test_entropy_hard_fail_blocks_gate() -> None:
    ev = OperationalRuntimeEvidence(max_entropy=0.35)
    report = compute_operational_stability(ev)
    assert report.gate_pass is False
    assert "entropy_max" in report.hard_failures[0]


def test_operational_score_reproducible(
    entropy_controller, truth_graph,
) -> None:
    params = load_window_params(MATRIX, "1h")
    repo = Path(__file__).resolve().parents[2]
    a = run_all_phases(params, repo, entropy_controller, truth_graph)
    b = run_all_phases(params, repo, entropy_controller, truth_graph)
    sa = compute_operational_stability(a.evidence)
    sb = compute_operational_stability(b.evidence)
    assert sa.score == sb.score
    assert sa.dimensions == sb.dimensions


def test_simulated_phases_integrate_with_semantic_stability(
    entropy_controller, truth_graph,
) -> None:
    repo = Path(__file__).resolve().parents[2]
    params = load_window_params(MATRIX, "1h")
    phases = run_all_phases(params, repo, entropy_controller, truth_graph)
    semantic = evaluate_stability(entropy_controller, truth_graph)
    operational = evaluate_operational_stability(phases.evidence)
    assert semantic.gate_pass is True
    assert operational.score >= 0.85
    assert phases.entropy["pass"] is True
    assert phases.patch["pass"] is True
