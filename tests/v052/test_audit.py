"""Area 0: v052 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v052" / "audit"


def test_attention_memory_surface_exists() -> None:
    p = AUDIT / "attention_memory_surface.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.5.2"
    assert any("attention_memory_store" in s["path"] for s in data["consolidation_surfaces"])


def test_consolidation_flow_docs() -> None:
    assert (AUDIT / "implicit_memory_consolidation_flow.md").is_file()
    assert (AUDIT / "consolidation_routing_inventory.md").is_file()
