"""MVP canary control flow with a fake transport. No live provider call."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hermes.orchestration.pilot_canary import render_mvp_report, run_mvp_canary


def test_missing_credential_does_not_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEAMOROUTER_API_KEY", raising=False)

    def _fail(_payload):
        raise AssertionError("canary called the provider without a credential")

    result = run_mvp_canary(post=_fail)
    assert result.blocked_reason == "CANARY_BLOCKED_NO_CREDENTIAL"
    assert result.conditions_met is False
    assert result.report.pilot_acceptance == "mvp_operator_reviewed"


def test_fake_transport_meets_mvp_conditions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEAMOROUTER_API_KEY", "sk-testcanaryvalue")
    calls = {"count": 0}

    def post(payload):
        assert "sk-testcanaryvalue" not in json_input(payload)
        calls["count"] += 1
        return 200, {"usage": {"total_tokens": 12}, "output_text": "proposal only"}

    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    sandbox = tmp_path / "sandbox"
    result = run_mvp_canary(post=post, sandbox_dir=sandbox)
    text = render_mvp_report(result)
    assert result.conditions_met, result.diagnostics
    assert calls["count"] == 5
    assert "sk-testcanaryvalue" not in text
    assert "proposal only" not in text
    assert "**pilot_acceptance:** mvp_operator_reviewed" in text
    assert "**review:** OPERATOR_SELF_REVIEW" in text
    assert "**independent_pass:** not_issued" in text
    assert "not a live Claude API" in text
    assert sentinel.read_text(encoding="utf-8") == "keep"
    denied = next(item for item in result.summaries if item.scenario_id == "unauthorized_action_block")
    assert denied.blocked is True
    assert denied.tool_executor_calls == 0
    files = next(item for item in result.summaries if item.scenario_id == "multi_file_refactor_rollback")
    assert files.file_ops_inside_sandbox is True
    assert files.replay_matched is True
    steering = next(item for item in result.summaries if item.scenario_id == "mid_turn_steering")
    assert steering.interrupt_ms is not None
    assert steering.interrupt_ms < 3000
    assert os.environ["TEAMOROUTER_API_KEY"] not in text


def json_input(payload: dict) -> str:
    value = payload.get("input")
    return value if isinstance(value, str) else ""
