from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from hermes.deliberation import run_deliberation, triage_task
from hermes.deliberation.children import run_children
from hermes.deliberation.judge import judge_children
from hermes.deliberation.trace import redact
from hermes.deliberation.verifier import verify_claims
from hermes.providers.cli_adapter import CLIProviderAdapter
from hermes.providers.cli_discovery import discover_cli_providers
from hermes.providers.base import ProviderTask


ROOT = Path(__file__).resolve().parents[1]


def test_cli_discovery_reports_missing_command_without_invoking_user_input() -> None:
    result = discover_cli_providers(
        {
            "missing_cli": {
                "enabled": False,
                "type": "cli",
                "command": "definitely-not-a-hermes-cli",
                "health_check": {"args": ["--version"]},
            }
        }
    )[0]
    assert result.provider_id == "missing_cli"
    assert result.found is False
    assert result.health == "unavailable"
    assert result.reason == "command_not_found"


def test_cli_discovery_rejects_unsafe_health_args() -> None:
    command = "cmd" if sys.platform.startswith("win") else "sh"
    result = discover_cli_providers(
        {
            "unsafe_cli": {
                "enabled": True,
                "type": "cli",
                "command": command,
                "health_check": {"args": ["/c", "echo unsafe"]},
            }
        }
    )[0]
    assert result.found is True
    assert result.health == "not_checked"
    assert result.reason == "unsafe_or_missing_health_check"


def test_disabled_cli_adapter_does_not_invoke() -> None:
    adapter = CLIProviderAdapter(
        "disabled",
        {"enabled": False, "command": "python", "invoke_template": ["-c", "print({task!r})"]},
    )
    result = adapter.invoke(ProviderTask("hello", dry_run=False))
    assert result.success is False
    assert result.error_type == "provider_disabled"


def test_cli_adapter_dry_run_uses_template_without_execution() -> None:
    adapter = CLIProviderAdapter(
        "dry",
        {"enabled": False, "command": sys.executable, "invoke_template": ["-c", "{task}"]},
    )
    result = adapter.invoke(ProviderTask("print('hello')", dry_run=True))
    assert result.success is True
    assert result.dry_run is True
    assert "dry_run" in result.output


def test_children_produce_independent_structured_outputs() -> None:
    children = run_children("implement provider policy", mode="full")
    assert [child["role"] for child in children] == ["engineering_child", "risk_child", "verification_child"]
    for child in children:
        assert {"answer", "assumptions", "risks", "verification_needed", "recommended_tests", "confidence"} <= set(child)


def test_judge_schema_flags_unsupported_claims() -> None:
    children = run_children("review provider cli policy", mode="full")
    judged = judge_children(children)
    assert {"consensus", "disagreements", "unsupported_claims", "shared_blindspots", "recommended_next_step"} <= set(judged)
    assert judged["unsupported_claims"]


def test_verifier_marks_claim_status() -> None:
    claims = ["CLI is installed", "Tests pass"]
    result = verify_claims(claims, {"cli is installed": True})
    assert result[0]["status"] == "verified"
    assert result[1]["status"] == "not_checked"


def test_trace_redaction_removes_secrets() -> None:
    redacted = redact({"api_key": "abc", "headers": {"Authorization": "Bearer secret-token"}})
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["headers"]["Authorization"] == "[REDACTED]"


def test_triage_escalates_state_change_to_guardian_required() -> None:
    triage = triage_task("implement and write files for provider changes")
    assert triage.guardian_required is True
    assert triage.route_mode == "guardian_required"


def test_run_deliberation_outputs_final_schema_and_trace(tmp_path: Path) -> None:
    result = run_deliberation(
        "Review provider cli architecture",
        mode="full",
        context={"trace_dir": tmp_path, "no_save_trace": False},
    ).to_dict()
    assert result["mode"] == "full"
    assert result["trace_id"]
    assert result["children_used"] == ["engineering_child", "risk_child", "verification_child"]
    assert Path(result["trace_path"]).is_file()


def test_hermes_deliberate_cli_json_no_save_trace() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hermes.py",
            "deliberate",
            "Review this provider registry design",
            "--mode",
            "full",
            "--dry-run",
            "--no-save-trace",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["mode"] == "full"
    assert "trace_path" not in payload
    assert payload["provider_discovery"]
