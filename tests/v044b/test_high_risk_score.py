"""Phase 8 — high-risk migration score."""

from __future__ import annotations

from observability.v04.authority_trace import AuthorityTrace
from observability.v04.high_risk_migration_score import (
    GATE_THRESHOLD,
    evaluate_high_risk_migration,
)


def test_score_shape_and_threshold():
    trace = AuthorityTrace()
    trace.record_guarded_operation(mutation_type="FILE_WRITE", target="governance_audit")
    report = evaluate_high_risk_migration(trace=trace)
    d = report.to_dict()
    assert d["gate_threshold"] == GATE_THRESHOLD
    assert "high_risk_coverage" in d["dimensions"]
    assert 0.0 <= d["score"] <= 1.0


def test_score_gate_when_trace_populated():
    trace = AuthorityTrace()
    for _ in range(3):
        trace.record_guarded_operation(mutation_type="REGISTRY_MUTATION", target="skill_registry")
    report = evaluate_high_risk_migration(trace=trace)
    assert report.score >= 0.5
