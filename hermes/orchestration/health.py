"""Provider health checks."""

from __future__ import annotations

from hermes.orchestration.adapters import ProviderAdapter


class ProviderHealthChecker:
    """Small health-check coordinator with test-friendly overrides."""

    def __init__(self, overrides: dict[str, tuple[bool, str]] | None = None):
        self.overrides = overrides or {}

    def check(self, adapter: ProviderAdapter) -> tuple[bool, str]:
        if adapter.name in self.overrides:
            return self.overrides[adapter.name]
        return adapter.health_check()
