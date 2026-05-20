"""Phase 9 — migration score."""

from __future__ import annotations

from observability.v04.migration_score import evaluate_migration, GATE_THRESHOLD


def test_migration_score_evaluates():
    report = evaluate_migration(regression_stable=True)
    d = report.to_dict()
    assert d["gate_threshold"] == GATE_THRESHOLD
    assert "mutation_coverage" in d["dimensions"]
    assert "authority_infrastructure" in d["dimensions"]
    assert d["score"] > 0.0
