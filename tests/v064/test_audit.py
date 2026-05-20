"""Area 0: v064 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v064" / "audit"


def test_reflection_surface_inventory_exists() -> None:
    p = AUDIT / "reflection_surface_inventory.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.4"
    assert any(
        "metacognitive_reflection" in s["path"] for s in data["reflection_surfaces"]
    )


def test_reflection_boundary_docs() -> None:
    assert (AUDIT / "reflection_boundary_report.md").is_file()
    assert (AUDIT / "degradation_pathology_map.md").is_file()
