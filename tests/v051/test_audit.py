"""Area 0: v051 audit artifacts (read-only)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v051" / "audit"


def test_runtime_attention_surface_exists() -> None:
    p = AUDIT / "runtime_attention_surface.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.5.1"
    assert any(s["path"].endswith("attention_kernel.py") for s in data["runtime_surfaces"])


def test_implicit_flow_and_routing_docs() -> None:
    assert (AUDIT / "implicit_attention_flow.md").is_file()
    assert (AUDIT / "attention_routing_inventory.md").is_file()
