from pathlib import Path

from hermes.release import compute_rc_health, generate_release_report


def test_rc_health_marks_release_ready() -> None:
    payload = compute_rc_health()
    assert payload["rc_health"] >= 85
    assert payload["release_ready"] is True
    assert "graph_health" in payload["components"]
    assert "dmn_health" in payload["components"]


def test_release_report_generates(tmp_path: Path) -> None:
    payload = generate_release_report(tmp_path / "release.md")
    assert Path(payload["report_path"]).is_file()
    assert Path(payload["json_path"]).is_file()
    text = Path(payload["report_path"]).read_text(encoding="utf-8")
    assert "v0.9 Release Report" in text
