"""Area 0: v060 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v060" / "audit"


def test_cognitive_governance_surface_exists() -> None:
    p = AUDIT / "cognitive_governance_surface.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.0"
    assert any("cognitive_governor" in s["path"] for s in data["governance_surfaces"])


def test_governance_flow_docs() -> None:
    assert (AUDIT / "implicit_governance_flow.md").is_file()
    assert (AUDIT / "governance_routing_inventory.md").is_file()
