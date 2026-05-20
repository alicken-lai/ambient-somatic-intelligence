"""Area 1: Phase 0 audit artifacts."""

from pathlib import Path


def test_runtime_soak_inventory() -> None:
    p = Path("v065c/audit/runtime_soak_inventory.json")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "0.6.5c" in text
    assert "karpathy_guidelines" in text


def test_audit_markdown_present() -> None:
    for name in (
        "precedence_conflict_report.md",
        "external_drift_surface_map.md",
        "runtime_authority_matrix.md",
    ):
        assert Path(f"v065c/audit/{name}").is_file()
