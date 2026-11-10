from pathlib import Path

from hermes.graph import compute_graph_health, generate_graph_health_report


def test_graph_health_has_coverage_metrics() -> None:
    payload = compute_graph_health()
    assert payload["graph_health"] >= 75
    assert payload["coverage"]["node_coverage"] > 0
    assert payload["coverage"]["relationship_coverage"] > 0
    assert isinstance(payload["isolated_nodes"], list)


def test_graph_health_report_generates(tmp_path: Path) -> None:
    payload = generate_graph_health_report(tmp_path / "graph.md")
    assert Path(payload["report_path"]).is_file()
    assert Path(payload["json_path"]).is_file()
    text = Path(payload["report_path"]).read_text(encoding="utf-8")
    assert "Graph Health" in text
