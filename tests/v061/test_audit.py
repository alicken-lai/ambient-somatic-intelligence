"""Area 0: v061 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v061" / "audit"


def test_constitutional_governance_surface_exists() -> None:
    p = AUDIT / "constitutional_governance_surface.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.6.1"
    assert any("constitutional_guard" in s["path"] for s in data["constitutional_surfaces"])


def test_constitutional_flow_docs() -> None:
    assert (AUDIT / "implicit_constitutional_flow.md").is_file()
    assert (AUDIT / "constitutional_routing_inventory.md").is_file()
    assert (AUDIT / "constitutional_boundary_inventory.md").is_file()
