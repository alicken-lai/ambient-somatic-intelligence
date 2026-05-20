"""Area 0: v054 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v054" / "audit"


def test_cognitive_calibration_surface_exists() -> None:
    p = AUDIT / "cognitive_calibration_surface.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.5.4"
    assert any("confidence_cap" in s["path"] for s in data["calibration_surfaces"])


def test_calibration_flow_docs() -> None:
    assert (AUDIT / "implicit_calibration_flow.md").is_file()
    assert (AUDIT / "calibration_routing_inventory.md").is_file()
