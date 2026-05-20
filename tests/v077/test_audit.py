"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_agency_boundary_inventory() -> None:
    p = Path("v077/audit/agency_boundary_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.7" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "autonomous_agency_risk_report.md",
        "civilization_agency_risk_map.md",
        "recursive_agency_matrix.md",
    ):
        assert Path(f"v077/audit/{name}").is_file()
