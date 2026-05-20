"""Phase 0 — mutation surface reconciliation artifacts."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v044b" / "audit"


def test_reconciliation_artifacts_exist():
    assert (AUDIT / "mutation_surface_reconciliation.json").is_file()
    assert (AUDIT / "missing_mutation_paths.json").is_file()
    assert (AUDIT / "inventory_gap_report.md").is_file()


def test_reconciliation_documents_857_gap():
    data = json.loads((AUDIT / "mutation_surface_reconciliation.json").read_text())
    assert data["v043_total_scanned_mutations"] == 857
    assert data["v044_catalogued_paths"] == 500
    assert data["metadata_gap_857_vs_500"] == 357
    assert "gap_explanation" in data
    assert data["accounting_verdict"] in ("PASS_honest", "REVIEW")
