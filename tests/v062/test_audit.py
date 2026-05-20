"""Area 0: v062 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v062" / "audit"


def test_cognition_provenance_inventory_exists() -> None:
    p = AUDIT / "cognition_provenance_inventory.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.2"
    assert any("provenance_record" in s["path"] for s in data["provenance_surfaces"])


def test_identity_boundary_docs() -> None:
    assert (AUDIT / "identity_boundary_report.md").is_file()
    assert (AUDIT / "provenance_conflict_map.md").is_file()
    assert (AUDIT / "cognition_inheritance_matrix.md").is_file()
