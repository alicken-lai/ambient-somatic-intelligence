"""Phase 0 — legacy mutation inventory artifacts."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v044" / "audit"


def test_inventory_exists():
    assert (AUDIT / "legacy_mutation_inventory.json").is_file()
    assert (AUDIT / "mutation_classification_report.md").is_file()


def test_inventory_structure():
    data = json.loads((AUDIT / "legacy_mutation_inventory.json").read_text())
    assert data["version"] == "0.4.4"
    assert data["catalogued_paths"] == len(data["entries"])
    assert data["catalogued_paths"] > 0
    cats = {e["category"] for e in data["entries"]}
    assert "FILE_WRITE" in cats


def test_total_scanned_metadata():
    data = json.loads((AUDIT / "legacy_mutation_inventory.json").read_text())
    assert data["total_scanned_mutations"] >= data["catalogued_paths"]
