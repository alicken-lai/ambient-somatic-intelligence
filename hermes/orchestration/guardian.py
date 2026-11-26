"""Guardian enforcement seam for provider orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from hermes.orchestration.models import ProviderConfig, ProviderRequest
from hermes.orchestration.capabilities import MATERIAL_ACTION_CAPABILITIES


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
    authorization_ref: str | None = None
    authorization_version: str | None = None
    authorization_scope_digest: str | None = None
    issuer_id: str | None = None


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
        authorization_ref: str | None = None,
        authorization_version: str | None = None,
        issuer_id: str = "static-guardian:test-helper",
    ):
        self.result = GuardianResult(
            decision=GuardianDecision(decision),
            reason=reason,
            matched_policy=matched_policy,
            authorization_ref=authorization_ref,
            authorization_version=authorization_version,
            issuer_id=issuer_id,
        )

    def check(
        self,
        *,
        request: ProviderRequest,
        provider: ProviderConfig,
        capabilities: set[str],
        dry_run: bool,
    ) -> GuardianResult:
        if self.result.decision != GuardianDecision.ALLOW:
            return self.result
        proposal = request.proposed_action
        scope_digest = (
            proposal.authorization_scope_digest(
                provider_id=provider.provider_id,
                capabilities=capabilities,
            )
            if proposal is not None
            else None
        )
        return GuardianResult(
            decision=self.result.decision,
            reason=self.result.reason,
            matched_policy=self.result.matched_policy,
            authorization_ref=self.result.authorization_ref or "static-guardian:test-allow",
            authorization_version=self.result.authorization_version or "1",
            authorization_scope_digest=scope_digest,
            issuer_id=self.result.issuer_id,
        )


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


DANGEROUS_CAPABILITIES = MATERIAL_ACTION_CAPABILITIES
