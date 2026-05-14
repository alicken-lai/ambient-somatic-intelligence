"""
Permission Enforcer — Runtime tool and interaction permission checks.

Wraps BoundaryRegistry validation into a higher-level API for checking tool
access, agent-to-agent interaction, and cross-agent state reads. Every check
is tracked in an internal report that can be retrieved for auditing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.isolation_kernel.boundary_definitions import (
    BoundaryRegistry,
    _tool_matches,
)

log = logging.getLogger(__name__)


@dataclass
class ToolAccessResult:
    allowed: bool
    agent_id: str
    tool_name: str
    reason: str
    policy_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "reason": self.reason,
            "policy_source": self.policy_source,
        }


@dataclass
class InteractionResult:
    allowed: bool
    source: str
    target: str
    interaction_type: str
    channel: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "source": self.source,
            "target": self.target,
            "interaction_type": self.interaction_type,
            "channel": self.channel,
            "reason": self.reason,
        }


@dataclass
class StateAccessResult:
    allowed: bool
    agent_id: str
    target_agent_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "agent_id": self.agent_id,
            "target_agent_id": self.target_agent_id,
            "reason": self.reason,
        }


@dataclass
class EnforcementReport:
    agent_id: str
    total_checks: int
    allowed: int
    denied: int
    violations: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "total_checks": self.total_checks,
            "allowed": self.allowed,
            "denied": self.denied,
            "violations": self.violations,
            "generated_at": self.generated_at,
        }


class PermissionEnforcer:
    """High-level permission enforcement combining boundary policies."""

    def __init__(self, registry: BoundaryRegistry) -> None:
        self._registry = registry
        self._checks: dict[str, list[dict[str, Any]]] = {}

    def check_tool_access(
        self,
        agent_id: str,
        tool_name: str,
        context: dict | None = None,
    ) -> ToolAccessResult:
        policy = self._registry.get_policy(agent_id)
        source = (
            "agent_policy"
            if agent_id in self._registry._policies
            else "default_policy"
        )

        for pattern in policy.denied_tools:
            if _tool_matches(tool_name, pattern):
                result = ToolAccessResult(
                    allowed=False,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    reason=f"Tool '{tool_name}' matches denied pattern '{pattern}'",
                    policy_source=source,
                )
                self._record_check(agent_id, "tool_access", result.allowed, result.reason)
                return result

        for pattern in policy.allowed_tools:
            if _tool_matches(tool_name, pattern):
                result = ToolAccessResult(
                    allowed=True,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    reason=f"Tool '{tool_name}' matches allowed pattern '{pattern}'",
                    policy_source=source,
                )
                self._record_check(agent_id, "tool_access", result.allowed, result.reason)
                return result

        result = ToolAccessResult(
            allowed=False,
            agent_id=agent_id,
            tool_name=tool_name,
            reason=f"Tool '{tool_name}' not in allowed tools — default deny",
            policy_source=source,
        )
        self._record_check(agent_id, "tool_access", result.allowed, result.reason)
        return result

    def check_agent_interaction(
        self,
        source_agent: str,
        target_agent: str,
        interaction_type: str,
    ) -> InteractionResult:
        source_policy = self._registry.get_policy(source_agent)

        if interaction_type == "direct":
            result = InteractionResult(
                allowed=False,
                source=source_agent,
                target=target_agent,
                interaction_type=interaction_type,
                channel=None,
                reason="Direct agent-to-agent communication is not permitted",
            )
            self._record_check(source_agent, "agent_interaction", False, result.reason)
            return result

        channel = interaction_type if interaction_type in ("orchestrator", "bus_events") else None
        if channel and channel in source_policy.communication_channels:
            result = InteractionResult(
                allowed=True,
                source=source_agent,
                target=target_agent,
                interaction_type=interaction_type,
                channel=channel,
                reason=f"Interaction via '{channel}' is permitted",
            )
            self._record_check(source_agent, "agent_interaction", True, result.reason)
            return result

        if channel is None:
            result = InteractionResult(
                allowed=False,
                source=source_agent,
                target=target_agent,
                interaction_type=interaction_type,
                channel=None,
                reason=f"Unknown interaction type '{interaction_type}' — default deny",
            )
            self._record_check(source_agent, "agent_interaction", False, result.reason)
            return result

        result = InteractionResult(
            allowed=False,
            source=source_agent,
            target=target_agent,
            interaction_type=interaction_type,
            channel=channel,
            reason=(
                f"Channel '{channel}' not in allowed channels "
                f"{source_policy.communication_channels}"
            ),
        )
        self._record_check(source_agent, "agent_interaction", False, result.reason)
        return result

    def check_state_access(
        self,
        agent_id: str,
        target_agent_id: str,
    ) -> StateAccessResult:
        if agent_id == target_agent_id:
            result = StateAccessResult(
                allowed=True,
                agent_id=agent_id,
                target_agent_id=target_agent_id,
                reason="Self-access is always allowed",
            )
            self._record_check(agent_id, "state_access", True, result.reason)
            return result

        policy = self._registry.get_policy(agent_id)
        if policy.can_access_other_agent_state:
            result = StateAccessResult(
                allowed=True,
                agent_id=agent_id,
                target_agent_id=target_agent_id,
                reason="Policy grants cross-agent state access",
            )
            self._record_check(agent_id, "state_access", True, result.reason)
            return result

        result = StateAccessResult(
            allowed=False,
            agent_id=agent_id,
            target_agent_id=target_agent_id,
            reason="Policy denies cross-agent state access",
        )
        self._record_check(agent_id, "state_access", False, result.reason)
        return result

    def get_enforcement_report(self, agent_id: str) -> EnforcementReport:
        checks = self._checks.get(agent_id, [])
        allowed_count = sum(1 for c in checks if c["allowed"])
        denied_count = sum(1 for c in checks if not c["allowed"])
        violations = [c["reason"] for c in checks if not c["allowed"]]
        return EnforcementReport(
            agent_id=agent_id,
            total_checks=len(checks),
            allowed=allowed_count,
            denied=denied_count,
            violations=violations,
        )

    def _record_check(
        self,
        agent_id: str,
        check_type: str,
        allowed: bool,
        reason: str,
    ) -> None:
        if agent_id not in self._checks:
            self._checks[agent_id] = []
        self._checks[agent_id].append({
            "type": check_type,
            "allowed": allowed,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
