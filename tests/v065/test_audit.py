"""Area 0: v065 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v065" / "audit"


def test_homeostasis_surface_inventory_exists() -> None:
    p = AUDIT / "homeostasis_surface_inventory.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.5"
    assert any(
        "cognitive_homeostasis" in s["path"] for s in data["homeostasis_surfaces"]
    )


def test_stabilization_boundary_docs() -> None:
    assert (AUDIT / "stabilization_boundary_report.md").is_file()
    assert (AUDIT / "recovery_pressure_map.md").is_file()
