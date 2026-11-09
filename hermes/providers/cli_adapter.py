"""Governed CLI provider adapter."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Any

from hermes.providers.base import ProviderAdapter, ProviderHealth, ProviderResult, ProviderTask
from hermes.providers.cli_discovery import discover_cli_provider


SAFE_ENV_KEYS = {"PATH", "PATHEXT", "SystemRoot", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE"}


class CLIProviderAdapter(ProviderAdapter):
    """Invoke a configured CLI through whitelisted argv templates only."""

    def __init__(self, provider_id: str, config: dict[str, Any]):
        self.provider_id = provider_id
        self.config = config
        self.capabilities = list(config.get("capabilities", []))
        self.command = config.get("command")
        self.enabled = bool(config.get("enabled", False))

    def health_check(self) -> ProviderHealth:
        return discover_cli_provider(self.provider_id, self.config)

    def invoke(self, task: ProviderTask) -> ProviderResult:
        if task.dry_run:
            return ProviderResult(
                provider_id=self.provider_id,
                role=task.role,
                success=True,
                output=self._dry_run_output(task),
                trace_id=task.trace_id,
                dry_run=True,
            )
        if not self.enabled:
            return self._error(task, "provider_disabled")
        if not isinstance(self.command, str) or not shutil.which(self.command):
            return self._error(task, "command_not_found")
        argv = self._build_argv(task)
        if argv is None:
            return self._error(task, "missing_whitelisted_invoke_template")

        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                text=True,
                capture_output=True,
                timeout=task.timeout_seconds,
                env=_sanitized_env(),
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ProviderResult(
                provider_id=self.provider_id,
                role=task.role,
                success=False,
                latency_ms=int((time.monotonic() - started) * 1000),
                error_type="timeout",
                trace_id=task.trace_id,
            )
        output = (completed.stdout or "")[: task.max_output_chars]
        stderr = (completed.stderr or "").strip()[:1000]
        return ProviderResult(
            provider_id=self.provider_id,
            role=task.role,
            success=completed.returncode == 0,
            output=output,
            stderr_summary=stderr,
            latency_ms=int((time.monotonic() - started) * 1000),
            token_estimate=max(1, len(output.split())) if output else None,
            exit_code=completed.returncode,
            error_type=None if completed.returncode == 0 else "nonzero_exit",
            trace_id=task.trace_id,
        )

    def _build_argv(self, task: ProviderTask) -> list[str] | None:
        template = self.config.get("invoke_template") or self.config.get("args_template")
        if not isinstance(template, list) or not all(isinstance(item, str) for item in template):
            return None
        if "{task}" not in template:
            return None
        command_path = shutil.which(str(self.command))
        if not command_path:
            return None
        return [command_path, *[task.task if item == "{task}" else item for item in template]]

    def _dry_run_output(self, task: ProviderTask) -> str:
        argv = self._build_argv(task)
        return f"dry_run:{argv!r}" if argv else "dry_run:no whitelisted invoke template"

    def _error(self, task: ProviderTask, error_type: str) -> ProviderResult:
        return ProviderResult(
            provider_id=self.provider_id,
            role=task.role,
            success=False,
            error_type=error_type,
            trace_id=task.trace_id,
        )


def _sanitized_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key in SAFE_ENV_KEYS}
