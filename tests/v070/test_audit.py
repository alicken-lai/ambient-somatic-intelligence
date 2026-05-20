"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_sovereign_interaction_inventory() -> None:
    p = Path("v070/audit/sovereign_interaction_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.0" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "constitutional_collision_report.md",
        "cognition_federation_risk_map.md",
        "inter_sovereign_boundary_matrix.md",
    ):
        assert Path(f"v070/audit/{name}").is_file()
