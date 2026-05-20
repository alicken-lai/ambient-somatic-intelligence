"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_semantic_continuity_inventory() -> None:
    p = Path("v073/audit/semantic_continuity_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.3" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "meaning_drift_report.md",
        "civilization_semantic_risk_map.md",
        "cross_epoch_meaning_matrix.md",
    ):
        assert Path(f"v073/audit/{name}").is_file()
