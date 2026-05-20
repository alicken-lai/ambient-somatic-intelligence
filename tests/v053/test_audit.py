"""Area 0: v053 audit artifacts."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "v053" / "audit"


def test_attention_forecasting_surface_exists() -> None:
    p = AUDIT / "attention_forecasting_surface.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.5.3"
    assert any("attention_forecast" in s["path"] for s in data["forecasting_surfaces"])


def test_forecast_flow_docs() -> None:
    assert (AUDIT / "implicit_forecast_flow.md").is_file()
    assert (AUDIT / "forecast_routing_inventory.md").is_file()
