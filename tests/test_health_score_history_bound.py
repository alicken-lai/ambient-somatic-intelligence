"""The serialized health snapshot must stay bounded as telemetry accumulates."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import health_score  # noqa: E402


def _entry(index: int) -> dict:
    return {"timestamp": f"entry-{index}", "health_score": float(index), "subsystems": {}}


def _result(history: list[dict]) -> dict:
    return {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "telemetry_count": len(history),
        "baseline": "guardian/baselines/telemetry_baseline.json",
        "history": history,
        "current": {
            "timestamp": "2026-01-01T00:00:00+00:00",
            "health_score": 75.61,
            "subsystems": {
                "cpu_health": {
                    "score": 80.0,
                    "raw_score": 85.0,
                    "incident_penalty": 0.0,
                    "incident_links": [],
                }
            },
        },
        "trend": "improving",
        "recommendations": ["observe memory_health"],
        "recommendations_only": True,
    }


def _redirect(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(health_score, "HEALTH_DIR", tmp_path)
    monkeypatch.setattr(health_score, "HEALTH_JSON", tmp_path / "health_scores.json")
    monkeypatch.setattr(health_score, "HEALTH_REPORT", tmp_path / "health_report.md")


def test_write_report_caps_history(tmp_path, monkeypatch):
    _redirect(monkeypatch, tmp_path)
    history = [_entry(i) for i in range(health_score.HISTORY_LIMIT + 50)]

    health_score.write_report(_result(history))

    written = json.loads((tmp_path / "health_scores.json").read_text(encoding="utf-8"))
    assert len(written["history"]) == health_score.HISTORY_LIMIT
    assert written["history"][0] == history[50]
    assert written["history"][-1] == history[-1]
    assert written["current"]["health_score"] == 75.61


def test_write_report_keeps_short_history(tmp_path, monkeypatch):
    _redirect(monkeypatch, tmp_path)
    history = [_entry(i) for i in range(3)]

    health_score.write_report(_result(history))

    written = json.loads((tmp_path / "health_scores.json").read_text(encoding="utf-8"))
    assert written["history"] == history


def test_report_still_lists_ten_recent_rows(tmp_path, monkeypatch):
    _redirect(monkeypatch, tmp_path)
    history = [_entry(i) for i in range(health_score.HISTORY_LIMIT + 10)]

    health_score.write_report(_result(history))

    report = (tmp_path / "health_report.md").read_text(encoding="utf-8")
    rows = [line for line in report.splitlines() if line.startswith("| entry-")]
    assert len(rows) == 10
