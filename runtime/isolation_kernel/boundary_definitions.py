"""
Isolation Boundary Definitions — Per-agent isolation policies and validation.

Defines what each agent can and cannot do across memory, tools, context, and
inter-agent communication. The BoundaryRegistry holds all policies and provides
default-deny validation: anything not explicitly allowed is denied.

Every validation produces a BoundaryCheckResult with a human-readable reason,
making all enforcement decisions auditable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class IsolationPolicy:
    agent_id: str
    allowed_memory_layers: list[str] = field(default_factory=list)
    readable_memory_layers: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)
    max_memory_writes_per_task: int = 10
    max_context_tokens: int = 64000
    can_access_other_agent_state: bool = False
    communication_channels: list[str] = field(default_factory=lambda: ["orchestrator"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "allowed_memory_layers": self.allowed_memory_layers,
            "readable_memory_layers": self.readable_memory_layers,
            "allowed_tools": self.allowed_tools,
            "denied_tools": self.denied_tools,
            "max_memory_writes_per_task": self.max_memory_writes_per_task,
            "max_context_tokens": self.max_context_tokens,
            "can_access_other_agent_state": self.can_access_other_agent_state,
            "communication_channels": self.communication_channels,
        }


@dataclass
class BoundaryCheckResult:
    allowed: bool
    agent_id: str
    action_type: str
    target: str
    reason: str
    policy_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "target": self.target,
            "reason": self.reason,
            "policy_source": self.policy_source,
        }


DEFAULT_AGENT_POLICIES: dict[str, IsolationPolicy] = {
    "frontend-agent": IsolationPolicy(
        agent_id="frontend-agent",
        allowed_memory_layers=["episodic", "procedural", "scratchpad"],
        readable_memory_layers=["episodic", "procedural", "semantic", "scratchpad"],
        allowed_tools=["file:read", "file:write", "shell:dev", "search:*"],
        denied_tools=["shell:destructive", "git:force", "file:delete_system"],
        max_memory_writes_per_task=10,
        max_context_tokens=64000,
        can_access_other_agent_state=False,
        communication_channels=["orchestrator"],
    ),
    "backend-agent": IsolationPolicy(
        agent_id="backend-agent",
        allowed_memory_layers=["episodic", "procedural", "scratchpad"],
        readable_memory_layers=["episodic", "procedural", "semantic", "scratchpad"],
        allowed_tools=["file:read", "file:write", "shell:dev", "search:*", "network:api"],
        denied_tools=["shell:destructive", "git:force", "file:delete_system"],
        max_memory_writes_per_task=15,
        max_context_tokens=96000,
        can_access_other_agent_state=False,
        communication_channels=["orchestrator"],
    ),
    "testing-agent": IsolationPolicy(
        agent_id="testing-agent",
        allowed_memory_layers=["episodic", "procedural", "scratchpad"],
        readable_memory_layers=["episodic", "procedural", "semantic", "scratchpad"],
        allowed_tools=["file:read", "file:write", "shell:exec", "shell:run", "search:*"],
        denied_tools=["shell:destructive", "git:force", "file:delete_system"],
        max_memory_writes_per_task=10,
        max_context_tokens=64000,
        can_access_other_agent_state=False,
        communication_channels=["orchestrator"],
    ),
    "guardian-agent": IsolationPolicy(
        agent_id="guardian-agent",
        allowed_memory_layers=["governance", "episodic", "procedural", "semantic"],
        readable_memory_layers=["episodic", "procedural", "semantic", "governance", "scratchpad"],
        allowed_tools=["file:read", "search:*", "memory:read", "governance:*"],
        denied_tools=["shell:destructive", "git:force"],
        max_memory_writes_per_task=20,
        max_context_tokens=96000,
        can_access_other_agent_state=True,
        communication_channels=["orchestrator", "bus_events"],
    ),
    "memory-agent": IsolationPolicy(
        agent_id="memory-agent",
        allowed_memory_layers=["episodic", "procedural", "semantic", "scratchpad", "archive"],
        readable_memory_layers=["episodic", "procedural", "semantic", "governance", "scratchpad", "archive"],
        allowed_tools=["memory:*", "file:read", "search:*"],
        denied_tools=["shell:destructive", "git:force", "file:delete_system"],
        max_memory_writes_per_task=50,
        max_context_tokens=128000,
        can_access_other_agent_state=False,
        communication_channels=["orchestrator"],
    ),
    "planner-agent": IsolationPolicy(
        agent_id="planner-agent",
        allowed_memory_layers=["episodic", "procedural", "scratchpad"],
        readable_memory_layers=["episodic", "procedural", "semantic", "scratchpad"],
        allowed_tools=["file:read", "search:*", "agent:spawn", "agent:pause", "agent:resume"],
        denied_tools=["shell:destructive", "git:force", "file:delete_system", "shell:exec", "file:write"],
        max_memory_writes_per_task=10,
        max_context_tokens=96000,
        can_access_other_agent_state=False,
        communication_channels=["orchestrator", "bus_events"],
    ),
}

_DEFAULT_POLICY = IsolationPolicy(
    agent_id="__default__",
    allowed_memory_layers=["scratchpad"],
    readable_memory_layers=["scratchpad"],
    allowed_tools=["file:read", "search:*"],
    denied_tools=["shell:destructive", "git:force", "file:delete_system"],
    max_memory_writes_per_task=5,
    max_context_tokens=32000,
    can_access_other_agent_state=False,
    communication_channels=["orchestrator"],
)


def _tool_matches(tool_name: str, pattern: str) -> bool:
    """Check if a tool name matches a pattern (supports trailing wildcard)."""
    if pattern.endswith(":*"):
        return tool_name.startswith(pattern[:-1])
    return tool_name == pattern


class BoundaryRegistry:
    """Registry of per-agent isolation policies with default-deny validation."""

    def __init__(self) -> None:
        self._policies: dict[str, IsolationPolicy] = dict(DEFAULT_AGENT_POLICIES)

    def register_policy(self, policy: IsolationPolicy) -> None:
        self._policies[policy.agent_id] = policy
        log.info("Registered isolation policy for %s", policy.agent_id)

    def get_policy(self, agent_id: str) -> IsolationPolicy:
        return self._policies.get(agent_id, self.get_default_policy())

    def get_default_policy(self) -> IsolationPolicy:
        return _DEFAULT_POLICY

    def validate_action(
        self,
        agent_id: str,
        action_type: str,
        target: str,
    ) -> BoundaryCheckResult:
        policy = self.get_policy(agent_id)
        source = "agent_policy" if agent_id in self._policies else "default_policy"

        if action_type == "memory_write":
            return self._validate_memory_write(policy, agent_id, target, source)
        if action_type == "memory_read":
            return self._validate_memory_read(policy, agent_id, target, source)
        if action_type == "tool_use":
            return self._validate_tool_use(policy, agent_id, target, source)
        if action_type == "agent_state_access":
            return self._validate_agent_state_access(policy, agent_id, target, source)
        if action_type == "communication":
            return self._validate_communication(policy, agent_id, target, source)

        return BoundaryCheckResult(
            allowed=False,
            agent_id=agent_id,
            action_type=action_type,
            target=target,
            reason=f"Unknown action type '{action_type}' — default deny",
            policy_source=source,
        )

    def _validate_memory_write(
        self, policy: IsolationPolicy, agent_id: str, layer: str, source: str,
    ) -> BoundaryCheckResult:
        allowed = layer in policy.allowed_memory_layers
        reason = (
            f"Layer '{layer}' is in allowed write layers"
            if allowed
            else f"Layer '{layer}' is not in allowed write layers {policy.allowed_memory_layers}"
        )
        return BoundaryCheckResult(
            allowed=allowed,
            agent_id=agent_id,
            action_type="memory_write",
            target=layer,
            reason=reason,
            policy_source=source,
        )

    def _validate_memory_read(
        self, policy: IsolationPolicy, agent_id: str, layer: str, source: str,
    ) -> BoundaryCheckResult:
        allowed = layer in policy.readable_memory_layers
        reason = (
            f"Layer '{layer}' is in readable layers"
            if allowed
            else f"Layer '{layer}' is not in readable layers {policy.readable_memory_layers}"
        )
        return BoundaryCheckResult(
            allowed=allowed,
            agent_id=agent_id,
            action_type="memory_read",
            target=layer,
            reason=reason,
            policy_source=source,
        )

    def _validate_tool_use(
        self, policy: IsolationPolicy, agent_id: str, tool_name: str, source: str,
    ) -> BoundaryCheckResult:
        for pattern in policy.denied_tools:
            if _tool_matches(tool_name, pattern):
                return BoundaryCheckResult(
                    allowed=False,
                    agent_id=agent_id,
                    action_type="tool_use",
                    target=tool_name,
                    reason=f"Tool '{tool_name}' matches denied pattern '{pattern}'",
                    policy_source=source,
                )

        for pattern in policy.allowed_tools:
            if _tool_matches(tool_name, pattern):
                return BoundaryCheckResult(
                    allowed=True,
                    agent_id=agent_id,
                    action_type="tool_use",
                    target=tool_name,
                    reason=f"Tool '{tool_name}' matches allowed pattern '{pattern}'",
                    policy_source=source,
                )

        return BoundaryCheckResult(
            allowed=False,
            agent_id=agent_id,
            action_type="tool_use",
            target=tool_name,
            reason=f"Tool '{tool_name}' not in allowed tools — default deny",
            policy_source=source,
        )

    def _validate_agent_state_access(
        self, policy: IsolationPolicy, agent_id: str, target_agent: str, source: str,
    ) -> BoundaryCheckResult:
        if agent_id == target_agent:
            return BoundaryCheckResult(
                allowed=True,
                agent_id=agent_id,
                action_type="agent_state_access",
                target=target_agent,
                reason="Self-access is always allowed",
                policy_source=source,
            )
        allowed = policy.can_access_other_agent_state
        reason = (
            "Policy grants cross-agent state access"
            if allowed
            else "Policy denies cross-agent state access"
        )
        return BoundaryCheckResult(
            allowed=allowed,
            agent_id=agent_id,
            action_type="agent_state_access",
            target=target_agent,
            reason=reason,
            policy_source=source,
        )

    def _validate_communication(
        self, policy: IsolationPolicy, agent_id: str, channel: str, source: str,
    ) -> BoundaryCheckResult:
        allowed = channel in policy.communication_channels
        reason = (
            f"Channel '{channel}' is in allowed channels"
            if allowed
            else f"Channel '{channel}' is not in allowed channels {policy.communication_channels}"
        )
        return BoundaryCheckResult(
            allowed=allowed,
            agent_id=agent_id,
            action_type="communication",
            target=channel,
            reason=reason,
            policy_source=source,
        )

    def stats(self) -> dict[str, Any]:
        return {
            "registered_policies": len(self._policies),
            "agent_ids": sorted(self._policies.keys()),
        }
