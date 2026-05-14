"""
Tool Permission Matrix — Per-agent tool access control.

Defines which tools each agent is allowed to invoke, with three permission levels:
  ALLOWED         — Tool may be used freely
  DENIED          — Tool is blocked for this agent
  REQUIRES_REVIEW — Tool may be used only after human review/approval

Design:
  - Default-deny for unknown tools (safe by default)
  - Two-layer lookup: agent-specific overrides > default policy
  - Pre-loaded with sensible defaults for known agent roles
  - Grants/revokes are append-only (audit-friendly)

Usage:
    matrix = ToolPermissionMatrix()
    result = matrix.check("frontend-agent", "shell:exec")
    if result.permission == ToolPermission.DENIED:
        print(f"DENIED: {result.reason}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ToolPermission(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


@dataclass
class PermissionResult:
    """Result of a tool permission check."""
    permission: ToolPermission
    agent_id: str
    tool_name: str
    reason: str
    source: str = "default"  # "default", "agent_override", "grant", "revoke"

    @property
    def is_allowed(self) -> bool:
        return self.permission == ToolPermission.ALLOWED

    @property
    def is_denied(self) -> bool:
        return self.permission == ToolPermission.DENIED

    @property
    def needs_review(self) -> bool:
        return self.permission == ToolPermission.REQUIRES_REVIEW

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission": self.permission.value,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "reason": self.reason,
            "source": self.source,
        }


# ── Default tool categories ─────────────────────────────────────────────────

TOOL_CATEGORIES: dict[str, list[str]] = {
    "readonly": [
        "file:read", "search:grep", "search:glob", "search:semantic",
        "memory:read", "memory:recall", "context:assemble",
    ],
    "write": [
        "file:write", "file:create", "file:edit",
    ],
    "system": [
        "shell:exec", "shell:run", "process:kill", "system:config",
    ],
    "git": [
        "git:commit", "git:push", "git:branch", "git:merge", "git:checkout",
    ],
    "network": [
        "network:fetch", "network:curl", "network:api",
    ],
    "security": [
        "governance:policy", "governance:audit", "governance:gate",
        "anomaly:check", "anomaly:reset",
    ],
    "agent": [
        "agent:spawn", "agent:pause", "agent:resume", "agent:terminate",
    ],
    "messaging": [
        "messages:send", "messages:read",
    ],
}

# ── Default permission policies per agent role ───────────────────────────────

DEFAULT_POLICY: dict[str, ToolPermission] = {
    "file:read": ToolPermission.ALLOWED,
    "search:grep": ToolPermission.ALLOWED,
    "search:glob": ToolPermission.ALLOWED,
    "search:semantic": ToolPermission.ALLOWED,
    "memory:read": ToolPermission.ALLOWED,
    "memory:recall": ToolPermission.ALLOWED,
    "context:assemble": ToolPermission.ALLOWED,
    "file:write": ToolPermission.REQUIRES_REVIEW,
    "file:create": ToolPermission.REQUIRES_REVIEW,
    "file:edit": ToolPermission.REQUIRES_REVIEW,
    "shell:exec": ToolPermission.REQUIRES_REVIEW,
    "shell:run": ToolPermission.REQUIRES_REVIEW,
    "git:commit": ToolPermission.REQUIRES_REVIEW,
    "git:push": ToolPermission.REQUIRES_REVIEW,
    "git:branch": ToolPermission.ALLOWED,
    "git:merge": ToolPermission.REQUIRES_REVIEW,
    "git:checkout": ToolPermission.ALLOWED,
    "network:fetch": ToolPermission.REQUIRES_REVIEW,
    "network:curl": ToolPermission.REQUIRES_REVIEW,
    "network:api": ToolPermission.REQUIRES_REVIEW,
    "process:kill": ToolPermission.DENIED,
    "system:config": ToolPermission.DENIED,
    "governance:policy": ToolPermission.DENIED,
    "governance:audit": ToolPermission.ALLOWED,
    "governance:gate": ToolPermission.ALLOWED,
    "anomaly:check": ToolPermission.ALLOWED,
    "anomaly:reset": ToolPermission.DENIED,
    "agent:spawn": ToolPermission.REQUIRES_REVIEW,
    "agent:pause": ToolPermission.REQUIRES_REVIEW,
    "agent:resume": ToolPermission.ALLOWED,
    "agent:terminate": ToolPermission.DENIED,
    "messages:send": ToolPermission.REQUIRES_REVIEW,
    "messages:read": ToolPermission.ALLOWED,
}

AGENT_OVERRIDES: dict[str, dict[str, ToolPermission]] = {
    "guardian-agent": {
        "governance:policy": ToolPermission.ALLOWED,
        "anomaly:reset": ToolPermission.ALLOWED,
        "agent:terminate": ToolPermission.REQUIRES_REVIEW,
        "process:kill": ToolPermission.REQUIRES_REVIEW,
        "system:config": ToolPermission.REQUIRES_REVIEW,
    },
    "frontend-agent": {
        "shell:exec": ToolPermission.DENIED,
        "process:kill": ToolPermission.DENIED,
        "system:config": ToolPermission.DENIED,
        "network:fetch": ToolPermission.ALLOWED,
        "file:write": ToolPermission.ALLOWED,
        "file:create": ToolPermission.ALLOWED,
        "file:edit": ToolPermission.ALLOWED,
    },
    "backend-agent": {
        "shell:exec": ToolPermission.REQUIRES_REVIEW,
        "network:api": ToolPermission.ALLOWED,
        "file:write": ToolPermission.ALLOWED,
        "file:create": ToolPermission.ALLOWED,
        "file:edit": ToolPermission.ALLOWED,
    },
    "testing-agent": {
        "shell:exec": ToolPermission.ALLOWED,
        "shell:run": ToolPermission.ALLOWED,
        "file:write": ToolPermission.ALLOWED,
        "file:create": ToolPermission.ALLOWED,
        "file:edit": ToolPermission.ALLOWED,
    },
    "memory-agent": {
        "memory:read": ToolPermission.ALLOWED,
        "memory:recall": ToolPermission.ALLOWED,
        "file:write": ToolPermission.ALLOWED,
        "shell:exec": ToolPermission.DENIED,
    },
    "planner-agent": {
        "agent:spawn": ToolPermission.ALLOWED,
        "agent:pause": ToolPermission.ALLOWED,
        "shell:exec": ToolPermission.DENIED,
        "file:write": ToolPermission.DENIED,
    },
}


class ToolPermissionMatrix:
    """
    Per-agent tool permission matrix with default-deny for unknown tools.

    Lookup order:
      1. Runtime grants/revokes (highest priority)
      2. Agent-specific overrides (AGENT_OVERRIDES)
      3. Default policy (DEFAULT_POLICY)
      4. Default-deny for unknown tools
    """

    def __init__(
        self,
        default_policy: dict[str, ToolPermission] | None = None,
        agent_overrides: dict[str, dict[str, ToolPermission]] | None = None,
    ):
        self._default_policy = dict(default_policy or DEFAULT_POLICY)
        self._agent_overrides = {
            k: dict(v) for k, v in (agent_overrides or AGENT_OVERRIDES).items()
        }
        self._runtime_grants: dict[str, dict[str, ToolPermission]] = {}
        self._audit_trail: list[dict[str, Any]] = []

    def check(self, agent_id: str, tool_name: str) -> PermissionResult:
        """
        Check whether an agent may use a specific tool.

        Returns PermissionResult with the effective permission and its source.
        """
        # 1. Runtime grants/revokes
        if agent_id in self._runtime_grants:
            if tool_name in self._runtime_grants[agent_id]:
                perm = self._runtime_grants[agent_id][tool_name]
                return PermissionResult(
                    permission=perm,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    reason=f"Runtime {'grant' if perm != ToolPermission.DENIED else 'revoke'}",
                    source="runtime",
                )

        # 2. Agent-specific overrides
        if agent_id in self._agent_overrides:
            if tool_name in self._agent_overrides[agent_id]:
                perm = self._agent_overrides[agent_id][tool_name]
                return PermissionResult(
                    permission=perm,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    reason=f"Agent override for {agent_id}",
                    source="agent_override",
                )

        # 3. Default policy
        if tool_name in self._default_policy:
            perm = self._default_policy[tool_name]
            return PermissionResult(
                permission=perm,
                agent_id=agent_id,
                tool_name=tool_name,
                reason="Default policy",
                source="default",
            )

        # 4. Default-deny for unknown tools
        return PermissionResult(
            permission=ToolPermission.DENIED,
            agent_id=agent_id,
            tool_name=tool_name,
            reason=f"Unknown tool '{tool_name}' — default deny",
            source="default_deny",
        )

    def grant(self, agent_id: str, tool_name: str, permission: ToolPermission = ToolPermission.ALLOWED) -> None:
        """Grant a tool permission to an agent at runtime."""
        if agent_id not in self._runtime_grants:
            self._runtime_grants[agent_id] = {}
        self._runtime_grants[agent_id][tool_name] = permission
        self._audit_trail.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "grant",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "permission": permission.value,
        })

    def revoke(self, agent_id: str, tool_name: str) -> None:
        """Revoke a tool permission from an agent at runtime."""
        if agent_id not in self._runtime_grants:
            self._runtime_grants[agent_id] = {}
        self._runtime_grants[agent_id][tool_name] = ToolPermission.DENIED
        self._audit_trail.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "revoke",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "permission": ToolPermission.DENIED.value,
        })

    def list_permissions(self, agent_id: str) -> dict[str, str]:
        """List effective permissions for an agent across all known tools."""
        all_tools = set(self._default_policy.keys())
        if agent_id in self._agent_overrides:
            all_tools.update(self._agent_overrides[agent_id].keys())
        if agent_id in self._runtime_grants:
            all_tools.update(self._runtime_grants[agent_id].keys())

        return {
            tool: self.check(agent_id, tool).permission.value
            for tool in sorted(all_tools)
        }

    def stats(self) -> dict[str, Any]:
        """Permission matrix statistics."""
        return {
            "default_policy_size": len(self._default_policy),
            "agent_overrides": {k: len(v) for k, v in self._agent_overrides.items()},
            "runtime_grants": {k: len(v) for k, v in self._runtime_grants.items()},
            "audit_trail_size": len(self._audit_trail),
            "tool_categories": {k: len(v) for k, v in TOOL_CATEGORIES.items()},
        }
