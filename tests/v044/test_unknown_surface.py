"""Phase 5 — unknown mutation surface report."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_unknown_report_exists():
    path = REPO / "v044" / "audit" / "unknown_mutation_report.json"
    assert path.is_file()
    data = json.loads(path.read_text())
    assert "by_disposition" in data
    for label in ("SAFE", "MIGRATE", "DEPRECATED", "EXPERIMENTAL"):
        assert label in data["by_disposition"]
