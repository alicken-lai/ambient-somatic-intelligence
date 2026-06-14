from __future__ import annotations

import subprocess
import sys
from typing import Any

from hermes.providers.cli_adapter import CLIProviderAdapter
from hermes.providers.base import ProviderTask


def test_cli_provider_uses_shell_false_timeout_and_sanitized_env(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv: list[str], **kwargs: Any) -> Completed:
        captured["argv"] = argv
        captured.update(kwargs)
        return Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    adapter = CLIProviderAdapter(
        "safe",
        {"enabled": True, "command": sys.executable, "invoke_template": ["-c", "{task}"]},
    )
    result = adapter.invoke(ProviderTask("print('ok')", timeout_seconds=3))
    assert result.success is True
    assert captured["shell"] is False
    assert captured["timeout"] == 3
    assert "env" in captured
    assert all("KEY" not in key and "TOKEN" not in key and "SECRET" not in key for key in captured["env"])


def test_cli_provider_truncates_output(monkeypatch: Any) -> None:
    class Completed:
        returncode = 0
        stdout = "x" * 100
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Completed())
    adapter = CLIProviderAdapter(
        "truncate",
        {"enabled": True, "command": sys.executable, "invoke_template": ["-c", "{task}"]},
    )
    result = adapter.invoke(ProviderTask("print('x')", max_output_chars=10))
    assert result.output == "x" * 10


def test_cli_provider_requires_whitelisted_template() -> None:
    adapter = CLIProviderAdapter("no-template", {"enabled": True, "command": sys.executable})
    result = adapter.invoke(ProviderTask("hello"))
    assert result.success is False
    assert result.error_type == "missing_whitelisted_invoke_template"


def test_cli_provider_handles_timeout(monkeypatch: Any) -> None:
    def raise_timeout(*args: Any, **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(cmd="x", timeout=1)

    monkeypatch.setattr(subprocess, "run", raise_timeout)
    adapter = CLIProviderAdapter(
        "timeout",
        {"enabled": True, "command": sys.executable, "invoke_template": ["-c", "{task}"]},
    )
    result = adapter.invoke(ProviderTask("print('slow')", timeout_seconds=1))
    assert result.success is False
    assert result.error_type == "timeout"
