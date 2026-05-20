"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_purpose_boundary_inventory() -> None:
    p = Path("v076/audit/purpose_boundary_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.6" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "autonomous_purpose_risk_report.md",
        "civilization_teleology_risk_map.md",
        "motivational_recursion_matrix.md",
    ):
        assert Path(f"v076/audit/{name}").is_file()
