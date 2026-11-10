"""Guardian enforcement seam for provider orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from hermes.orchestration.models import ProviderConfig, ProviderRequest


class GuardianDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCK = "BLOCK"
    NOT_CHECKED = "NOT_CHECKED"


@dataclass(frozen=True)
class GuardianResult:
    decision: GuardianDecision
    reason: str = ""
    matched_policy: str | None = None


class GuardianChecker(Protocol):
    """Replaceable interface for Hermes Guardian/MCP enforcement."""

    def check(
        self,
        *,
        request: ProviderRequest,
        provider: ProviderConfig,
        capabilities: set[str],
        dry_run: bool,
    ) -> GuardianResult:
        """Return the Guardian decision for the selected route."""


class StaticGuardian:
    """Test helper that returns one fixed decision."""

    def __init__(
        self,
        decision: GuardianDecision | str,
        *,
        reason: str = "",
        matched_policy: str | None = None,
    ):
        self.result = GuardianResult(
            decision=GuardianDecision(decision),
            reason=reason,
            matched_policy=matched_policy,
        )

    def check(
        self,
        *,
        request: ProviderRequest,
        provider: ProviderConfig,
        capabilities: set[str],
        dry_run: bool,
    ) -> GuardianResult:
        return self.result


class FailClosedGuardian:
    """Default invoke-mode Guardian until a real integration is injected."""

    def check(
        self,
        *,
        request: ProviderRequest,
        provider: ProviderConfig,
        capabilities: set[str],
        dry_run: bool,
    ) -> GuardianResult:
        return GuardianResult(
            decision=GuardianDecision.REVIEW_REQUIRED,
            reason="Guardian integration is not configured for dangerous invocation",
            matched_policy="fail_closed_no_guardian",
        )


class NoopPlanningGuardian:
    """Dry-run marker for planning-only routes that were not Guardian-approved."""

    def check(
        self,
        *,
        request: ProviderRequest,
        provider: ProviderConfig,
        capabilities: set[str],
        dry_run: bool,
    ) -> GuardianResult:
        return GuardianResult(
            decision=GuardianDecision.NOT_CHECKED,
            reason="dry-run planning only; Guardian approval was not requested",
            matched_policy="planning_only",
        )


DANGEROUS_CAPABILITIES = {
    "local_file_access",
    "repo_edit",
    "terminal",
    "filesystem",
    "test_runner",
    "local_sensitive",
    "mcp_tools",
}
