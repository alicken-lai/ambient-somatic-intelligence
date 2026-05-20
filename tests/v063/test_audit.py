"""Area 0: v063 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v063" / "audit"


def test_coherence_surface_inventory_exists() -> None:
    p = AUDIT / "coherence_surface_inventory.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.3"
    assert any("cognitive_coherence" in s["path"] for s in data["coherence_surfaces"])


def test_coherence_boundary_docs() -> None:
    assert (AUDIT / "coherence_boundary_report.md").is_file()
    assert (AUDIT / "contradiction_conflict_map.md").is_file()
