"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_temporal_continuity_inventory() -> None:
    p = Path("v072/audit/temporal_continuity_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.7.2" in text
    assert "forbidden_patterns" in text


def test_audit_markdown_present() -> None:
    for name in (
        "continuity_fragmentation_report.md",
        "civilization_memory_drift_map.md",
        "cross_epoch_boundary_matrix.md",
    ):
        assert Path(f"v072/audit/{name}").is_file()
