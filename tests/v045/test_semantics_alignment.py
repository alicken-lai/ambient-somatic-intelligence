"""Semantics alignment score vs gate evidence."""

from observability.v04.semantics_alignment import (
    SEMANTICS_ALIGNMENT_THRESHOLD,
    evaluate_semantics_alignment,
)


def test_clean_graph_semantics_aligned(truth_graph, entropy_controller) -> None:
    ent = entropy_controller.compute(truth_graph)
    alignment = evaluate_semantics_alignment(ent)
    assert alignment.score >= SEMANTICS_ALIGNMENT_THRESHOLD
    assert alignment.gate_pass is True
    assert not alignment.mismatches
