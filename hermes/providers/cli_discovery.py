"""Safe PATH discovery for configured CLI providers."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

import yaml

from hermes.providers.base import ProviderHealth


SAFE_HEALTH_ARGS = {
    ("--version",),
    ("version",),
    ("-v",),
    ("-V",),
}


def discover_from_registry(
    registry_path: str | Path = "config/provider_registry.yaml",
    *,
    timeout_seconds: float = 2.0,
) -> list[dict[str, Any]]:
    """Load configured CLI-like providers and health check only their safe commands."""

    raw = yaml.safe_load(Path(registry_path).read_text(encoding="utf-8")) or {}
    providers = raw.get("providers", raw)
    if not isinstance(providers, dict):
        return []
    cli_configs = {
        provider_id: config
        for provider_id, config in providers.items()
        if isinstance(config, dict) and config.get("command")
    }
    return [health.to_dict() for health in discover_cli_providers(cli_configs, timeout_seconds=timeout_seconds)]


def discover_cli_providers(
    provider_configs: dict[str, dict[str, Any]],
    *,
    timeout_seconds: float = 2.0,
) -> list[ProviderHealth]:
    """Discover configured commands from PATH and run safe health checks only."""

    return [
        discover_cli_provider(provider_id, config, timeout_seconds=timeout_seconds)
        for provider_id, config in provider_configs.items()
    ]


def discover_cli_provider(
    provider_id: str,
    config: dict[str, Any],
    *,
    timeout_seconds: float = 2.0,
) -> ProviderHealth:
    command = config.get("command")
    enabled = bool(config.get("enabled", False))
    if not isinstance(command, str) or not command:
        return ProviderHealth(provider_id=provider_id, enabled=enabled, reason="missing_command")
    found_path = shutil.which(command)
    if not found_path:
        return ProviderHealth(
            provider_id=provider_id,
            command=command,
            enabled=enabled,
            found=False,
            health="unavailable",
            reason="command_not_found",
        )

    args = _health_args(config)
    if tuple(args) not in SAFE_HEALTH_ARGS:
        return ProviderHealth(
            provider_id=provider_id,
            command=command,
            enabled=enabled,
            found=True,
            health="not_checked",
            reason="unsafe_or_missing_health_check",
        )

    started = time.monotonic()
    try:
        completed = subprocess.run(
            [found_path, *args],
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ProviderHealth(
            provider_id=provider_id,
            command=command,
            enabled=enabled,
            found=True,
            health="timeout",
            reason="health_check_timeout",
            latency_ms=int((time.monotonic() - started) * 1000),
        )
    output = (completed.stdout or completed.stderr or "").strip()
    health = "ok" if completed.returncode == 0 else "failed"
    reason = "enabled" if enabled and health == "ok" else "found_but_not_enabled"
    if health != "ok":
        reason = "health_check_failed"
    return ProviderHealth(
        provider_id=provider_id,
        command=command,
        enabled=enabled,
        found=True,
        health=health,
        version=output[:500] or None,
        reason=reason,
        latency_ms=int((time.monotonic() - started) * 1000),
    )


def _health_args(config: dict[str, Any]) -> list[str]:
    raw = config.get("health_check", {})
    if isinstance(raw, dict):
        args = raw.get("args", ["--version"])
    else:
        args = ["--version"]
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        return []
    return args
