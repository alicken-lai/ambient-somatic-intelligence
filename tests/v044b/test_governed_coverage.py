"""Phase 6 — governed coverage metrics."""

from __future__ import annotations

from observability.v04.governed_coverage import (
    OVERALL_COVERAGE_TARGET,
    TRACE_COVERAGE_TARGET,
    compute_governed_coverage,
)
from observability.v04.authority_trace import AuthorityTrace


def test_governed_coverage_shape():
    trace = AuthorityTrace()
    trace.record_guarded_operation(mutation_type="FILE_WRITE", target="memory")
    report = compute_governed_coverage(trace=trace)
    d = report.to_dict()
    assert d["high_risk_total"] >= 1
    assert 0.0 <= d["high_risk_coverage"] <= 1.0
    assert d["trace_coverage"] >= TRACE_COVERAGE_TARGET
    assert "targets" in d


def test_high_risk_coverage_in_scope():
    report = compute_governed_coverage()
    assert report.high_risk_coverage >= 0.85
