"""Provider adapter interfaces for callable Hermes providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderHealth:
    provider_id: str
    command: str | None = None
    found: bool = False
    health: str = "unknown"
    version: str | None = None
    enabled: bool = False
    reason: str = ""
    latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "command": self.command,
            "found": self.found,
            "health": self.health,
            "version": self.version,
            "enabled": self.enabled,
            "reason": self.reason,
            "latency_ms": self.latency_ms,
        }


@dataclass(frozen=True)
class ProviderTask:
    task: str
    role: str = "provider"
    trace_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 60.0
    max_output_chars: int = 12000
    dry_run: bool = False


@dataclass(frozen=True)
class ProviderResult:
    provider_id: str
    role: str
    success: bool
    output: str = ""
    stderr_summary: str = ""
    latency_ms: int = 0
    token_estimate: int | None = None
    exit_code: int | None = None
    error_type: str | None = None
    trace_id: str | None = None
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "role": self.role,
            "success": self.success,
            "output": self.output,
            "stderr_summary": self.stderr_summary,
            "latency_ms": self.latency_ms,
            "token_estimate": self.token_estimate,
            "exit_code": self.exit_code,
            "error_type": self.error_type,
            "trace_id": self.trace_id,
            "dry_run": self.dry_run,
        }


class ProviderAdapter(ABC):
    provider_id: str
    capabilities: list[str]

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Return provider health without mutating external state."""

    @abstractmethod
    def invoke(self, task: ProviderTask) -> ProviderResult:
        """Invoke a callable provider through its governed interface."""

    def supports(self, capability: str) -> bool:
        return capability in set(self.capabilities)
