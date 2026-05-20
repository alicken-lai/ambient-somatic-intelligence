"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_value_continuity_inventory() -> None:
    p = Path("v074/audit/value_continuity_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.4" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "ethical_drift_report.md",
        "civilization_value_risk_map.md",
        "cross_epoch_value_matrix.md",
    ):
        assert Path(f"v074/audit/{name}").is_file()
