"""
Unified Governance Router — Bridges legacy guardian_check with the new MandatoryGate.

The Ambient OS has two governance systems:
  1. Legacy: guardian/policy.yaml + scripts/guardian_check.py (keyword-based)
  2. New:    governance/ package (PolicyEngine + ExecutionValidator + ToolPermissions + MandatoryGate)

This router provides a single entry point that:
  - Routes new-style checks through MandatoryGate (full pipeline)
  - Provides legacy_check() for backward compatibility with Hermes MCP guardian_check
  - Maps between legacy result format and new GateResult format
  - Tracks routing statistics for migration observability

Usage:
    router = UnifiedRouter(mandatory_gate)
    result = router.check("git push origin main", agent_id="cursor-agent")

    # Legacy-compatible (used by Hermes MCP)
    legacy_result = router.legacy_check("git push origin main")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from governance.policy_engine import PolicyEngine, RiskLevel
from governance.mandatory_gate import MandatoryGate, GateResult

logger = logging.getLogger("governance.unified_router")


@dataclass
class RouterStats:
    """Tracks routing statistics for migration observability."""
    new_checks: int = 0
    legacy_checks: int = 0
    agreement_count: int = 0
    disagreement_count: int = 0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total(self) -> int:
        return self.new_checks + self.legacy_checks

    @property
    def agreement_rate(self) -> float:
        compared = self.agreement_count + self.disagreement_count
        return self.agreement_count / max(compared, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "new_checks": self.new_checks,
            "legacy_checks": self.legacy_checks,
            "total": self.total,
            "agreement_count": self.agreement_count,
            "disagreement_count": self.disagreement_count,
            "agreement_rate": round(self.agreement_rate, 4),
            "started_at": self.started_at,
        }


class UnifiedRouter:
    """
    Routes governance checks through the new system while maintaining
    backward compatibility with legacy guardian_check.

    The router always uses MandatoryGate for new-style checks and provides
    a legacy_check() method that maps results to the old format.
    """

    def __init__(
        self,
        mandatory_gate: MandatoryGate | None = None,
        legacy_policy_engine: PolicyEngine | None = None,
    ):
        self.mandatory_gate = mandatory_gate or MandatoryGate()
        self._legacy_engine = legacy_policy_engine
        self._stats = RouterStats()

    def check(
        self,
        action: str,
        agent_id: str = "unknown",
        tool_name: str | None = None,
        resource: str = "",
        scopes: list[str] | None = None,
        context: str = "",
    ) -> GateResult:
        """
        Primary governance check — routes through MandatoryGate.

        This is the preferred entry point for all new code.
        """
        self._stats.new_checks += 1

        result = self.mandatory_gate.check(
            action=action,
            agent_id=agent_id,
            tool_name=tool_name,
            resource=resource,
            scopes=scopes,
            context=context,
        )

        logger.debug(
            f"UnifiedRouter.check: action='{action[:60]}' agent={agent_id} "
            f"→ {result.risk_level.name} (allowed={result.allowed})"
        )

        return result

    def legacy_check(
        self,
        action: str,
        route_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Backward-compatible check matching the old guardian_check interface.

        Returns a dict with: risk, matched, action, reason, boundary_level
        (same shape as PolicyEngine.classify_action).

        Internally routes through MandatoryGate and maps the result.
        """
        self._stats.legacy_checks += 1

        gate_result = self.mandatory_gate.check(
            action=action,
            agent_id="legacy",
        )

        matched_policies: list[str] = []
        if gate_result.validation_result:
            for stage in gate_result.validation_result.stages:
                policy_name = stage.metadata.get("policy", "")
                if policy_name:
                    matched_policies.append(policy_name)

        legacy_result = {
            "risk": gate_result.risk_level.name,
            "matched": matched_policies,
            "action": action,
            "reason": gate_result.reason,
            "boundary_level": route_name or "OBSERVE_ONLY",
        }

        if self._legacy_engine:
            self._compare_with_legacy(action, route_name, gate_result)

        return legacy_result

    def _compare_with_legacy(
        self,
        action: str,
        route_name: str | None,
        new_result: GateResult,
    ) -> None:
        """Compare new system result with legacy for migration observability."""
        try:
            legacy = self._legacy_engine.classify_action(action, route_name)
            legacy_risk = legacy.get("risk", "ALLOW")
            new_risk = new_result.risk_level.name

            if legacy_risk == new_risk:
                self._stats.agreement_count += 1
            else:
                self._stats.disagreement_count += 1
                logger.info(
                    f"Router disagreement: action='{action[:60]}' "
                    f"legacy={legacy_risk} new={new_risk}"
                )
        except Exception as exc:
            logger.warning(f"Legacy comparison failed: {exc}")

    @property
    def stats(self) -> RouterStats:
        return self._stats

    def health(self) -> dict[str, Any]:
        """Health check for the unified router."""
        return {
            "router_active": True,
            "mandatory_gate_available": self.mandatory_gate is not None,
            "legacy_engine_available": self._legacy_engine is not None,
            "stats": self._stats.to_dict(),
            "gate_stats": self.mandatory_gate.stats() if self.mandatory_gate else None,
        }
