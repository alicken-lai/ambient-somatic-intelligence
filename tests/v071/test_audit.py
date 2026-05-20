"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_reality_alignment_inventory() -> None:
    p = Path("v071/audit/reality_alignment_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.1" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "divergence_surface_report.md",
        "operational_reality_risk_map.md",
        "cross_runtime_truth_matrix.md",
    ):
        assert Path(f"v071/audit/{name}").is_file()
