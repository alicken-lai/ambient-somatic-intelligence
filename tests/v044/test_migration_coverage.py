"""Phase 6 — migration coverage scanner."""

from __future__ import annotations

from observability.v04.migration_coverage import compute_migration_coverage, COVERAGE_GATE_THRESHOLD


def test_coverage_report_shape():
    report = compute_migration_coverage()
    d = report.to_dict()
    assert "coverage_ratio" in d
    assert 0.0 <= d["coverage_ratio"] <= 1.0
    assert d["gate_threshold"] == COVERAGE_GATE_THRESHOLD
    assert "by_category" in d
