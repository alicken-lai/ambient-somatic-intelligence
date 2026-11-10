from pathlib import Path

from hermes.audit import compute_institutional_health, generate_audit_report


def test_institutional_health_scores_required_dimensions() -> None:
    payload = compute_institutional_health()
    assert payload["institutional_health"] >= 80
    for key in [
        "integration",
        "governance",
        "observability",
        "knowledge_coverage",
        "identity_continuity",
        "auditability",
        "maintainability",
    ]:
        assert key in payload["components"]
    assert payload["strengths"]
    assert payload["risks"]


def test_audit_report_generates_markdown_and_json(tmp_path: Path) -> None:
    payload = generate_audit_report(tmp_path / "audit.md")
    assert Path(payload["report_path"]).is_file()
    assert Path(payload["json_path"]).is_file()
    text = Path(payload["report_path"]).read_text(encoding="utf-8")
    assert "Institutional Health" in text
    assert "v0.9 release candidate" in text
