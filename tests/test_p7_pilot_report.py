"""The checked-in P7 sandbox report must match the renderer."""

from __future__ import annotations

from pathlib import Path

from hermes.orchestration.pilot_report import render_sandbox_report
from hermes.orchestration.pilot_sandbox import SANDBOX_SECRET


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "p7" / "P7_SANDBOX_METRICS_REPORT_2026-11-20.md"


def test_sandbox_report_snapshot_matches_renderer() -> None:
    rendered = render_sandbox_report()
    assert SANDBOX_SECRET not in rendered
    assert "pilot_acceptance：** not_claimed" in rendered
    assert "REVIEW_STATUS：** AWAITING_INDEPENDENT_REVIEWER" in rendered
    assert "IMPLEMENTER_VERDICT：** NONE" in rendered
    assert "`cost_replay_coverage` | 1 | 1 | true | 1 |" in rendered
    assert "`human_interruption_latency_ms` | unobserved | 3000 | unobserved | 0 |" in rendered
    assert REPORT.read_text(encoding="utf-8") == rendered
