"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_intent_continuity_inventory() -> None:
    p = Path("v075/audit/intent_continuity_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.5" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "motivational_drift_report.md",
        "civilization_intent_risk_map.md",
        "cross_epoch_intent_matrix.md",
    ):
        assert Path(f"v075/audit/{name}").is_file()
