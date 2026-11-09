from __future__ import annotations

import json
from pathlib import Path

from hermes.deliberation import run_deliberation
from hermes.deliberation.trace import redact, save_trace


def test_trace_contains_required_audit_fields(tmp_path: Path) -> None:
    result = run_deliberation(
        "Review provider policy architecture",
        mode="full",
        context={"trace_dir": tmp_path},
    ).to_dict()
    trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
    for key in [
        "task",
        "route_reason",
        "children",
        "judge",
        "synthesizer",
        "timestamp",
        "trace_id",
        "latency_ms",
        "guardian",
    ]:
        assert key in trace
    assert trace["trace_id"] == result["trace_id"]


def test_trace_redacts_secret_shapes(tmp_path: Path) -> None:
    trace = {
        "trace_id": "trace-secret-test",
        "api_key": "key-value",
        "token": "token-value",
        "password": "pass-value",
        "headers": {"Authorization": "Bearer secret-value"},
        "env": {"PROVIDER_SECRET": "secret", "NORMAL": "ok"},
    }
    path = save_trace(trace, trace_dir=tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "key-value" not in text
    assert "token-value" not in text
    assert "pass-value" not in text
    assert "secret-value" not in text
    assert "Bearer [REDACTED]" not in text
    assert "PROVIDER_SECRET" in text
    assert "[REDACTED]" in text


def test_redact_masks_environment_secret_keys() -> None:
    redacted = redact({"env": {"OPENAI_API_KEY": "abc", "PATH": "ok"}})
    assert redacted["env"]["OPENAI_API_KEY"] == "[REDACTED]"
    assert redacted["env"]["PATH"] == "ok"
