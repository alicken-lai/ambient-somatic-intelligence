from pathlib import Path

from hermes.graph import generate_graph_health_report
from hermes.release import generate_release_report


def test_graph_health_report_is_stable_when_inputs_do_not_change(tmp_path: Path) -> None:
    path = tmp_path / "graph.md"
    first = generate_graph_health_report(path)
    first_text = Path(first["report_path"]).read_text(encoding="utf-8")
    second = generate_graph_health_report(path)
    second_text = Path(second["report_path"]).read_text(encoding="utf-8")
    assert first_text == second_text
    assert first["graph_health"] == second["graph_health"]


def test_release_report_is_stable_when_inputs_do_not_change(tmp_path: Path) -> None:
    path = tmp_path / "release.md"
    first = generate_release_report(path)
    first_text = Path(first["report_path"]).read_text(encoding="utf-8")
    second = generate_release_report(path)
    second_text = Path(second["report_path"]).read_text(encoding="utf-8")
    assert first_text == second_text
    assert first["rc_health"] == second["rc_health"]
