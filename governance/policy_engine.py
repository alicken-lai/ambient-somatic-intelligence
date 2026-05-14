"""
Policy Engine — Structured rule-based governance evaluation.

Replaces the keyword-matching guardian_check with a multi-dimensional policy system:
  - Named policies with scopes, conditions, and actions
  - Permission matrices (agent × resource × operation)
  - Contextual evaluation (time-of-day, system load, recent failures)
  - Policy priority and conflict resolution
  - Backward-compatible with existing guardian_check interface

Policy structure:
  Policy:
    name: str
    scope: list[str]           — what this policy applies to (e.g., ["file:write", "shell:*"])
    conditions: list[Condition] — when this policy triggers
    decision: RiskLevel        — ALLOW / REVIEW / BLOCK
    reason: str                — human-readable explanation
    priority: int              — higher priority wins conflicts
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
GUARDIAN_DIR = AMBIENT_ROOT / "guardian"
POLICY_FILE = GUARDIAN_DIR / "policy.yaml"


class RiskLevel(IntEnum):
    ALLOW = 0
    REVIEW_REQUIRED = 1
    BLOCK = 2

    @classmethod
    def from_str(cls, value: str) -> "RiskLevel":
        mapping = {
            "allow": cls.ALLOW,
            "review_required": cls.REVIEW_REQUIRED,
            "review": cls.REVIEW_REQUIRED,
            "block": cls.BLOCK,
        }
        return mapping.get(value.lower(), cls.REVIEW_REQUIRED)


@dataclass
class Condition:
    """A single condition that triggers a policy."""
    type: str  # "keyword", "regex", "scope", "agent", "resource", "time", "load"
    value: str
    negate: bool = False

    def evaluate(self, context: "EvalContext") -> bool:
        result = self._check(context)
        return not result if self.negate else result

    def _check(self, context: "EvalContext") -> bool:
        if self.type == "keyword":
            return self.value.lower() in context.action.lower()
        elif self.type == "regex":
            return bool(re.search(self.value, context.action, re.IGNORECASE))
        elif self.type == "scope":
            return any(self._scope_matches(self.value, s) for s in context.scopes)
        elif self.type == "agent":
            return context.agent_id == self.value or self.value == "*"
        elif self.type == "resource":
            return self.value in context.resource
        elif self.type == "path_pattern":
            return bool(re.match(self.value, context.resource))
        elif self.type == "consecutive_failures":
            return context.recent_failures >= int(self.value)
        return False

    @staticmethod
    def _scope_matches(pattern: str, scope: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith(":*"):
            prefix = pattern[:-1]
            return scope.startswith(prefix)
        return pattern == scope


@dataclass
class EvalContext:
    """Context for policy evaluation."""
    action: str
    agent_id: str = "unknown"
    scopes: list[str] = field(default_factory=list)
    resource: str = ""
    route: str = ""
    recent_failures: int = 0
    system_load: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """A single governance policy rule."""
    name: str
    scopes: list[str]
    conditions: list[Condition]
    decision: RiskLevel
    reason: str
    priority: int = 50
    enabled: bool = True

    def evaluate(self, context: EvalContext) -> bool:
        """Check if this policy's conditions are ALL met."""
        if not self.enabled:
            return False
        return all(c.evaluate(context) for c in self.conditions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "scopes": self.scopes,
            "decision": self.decision.name,
            "reason": self.reason,
            "priority": self.priority,
            "enabled": self.enabled,
        }


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    risk: RiskLevel
    matched_policies: list[Policy]
    action: str
    reason: str
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_allowed(self) -> bool:
        return self.risk == RiskLevel.ALLOW

    @property
    def is_blocked(self) -> bool:
        return self.risk == RiskLevel.BLOCK

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk": self.risk.name,
            "action": self.action,
            "reason": self.reason,
            "matched_policies": [p.name for p in self.matched_policies],
            "context": self.context,
        }


# Built-in policies (loaded at startup, can be extended via config)
BUILTIN_POLICIES: list[Policy] = [
    # === BLOCK policies (highest priority) ===
    Policy(
        name="block_destructive_system",
        scopes=["shell:*"],
        conditions=[Condition("regex", r"(rm\s+-rf\s+/|sudo\s+shutdown|mkfs|dd\s+if=)")],
        decision=RiskLevel.BLOCK,
        reason="Destructive system command detected",
        priority=100,
    ),
    Policy(
        name="block_credential_exfil",
        scopes=["shell:*", "file:read"],
        conditions=[Condition("regex", r"(\.env|credentials|secret|private_key|id_rsa)")],
        decision=RiskLevel.BLOCK,
        reason="Potential credential access/exfiltration",
        priority=95,
    ),
    Policy(
        name="block_database_drop",
        scopes=["shell:*"],
        conditions=[Condition("regex", r"(drop\s+(database|table)|truncate\s+table)")],
        decision=RiskLevel.BLOCK,
        reason="Database destruction command detected",
        priority=100,
    ),
    Policy(
        name="block_force_push_main",
        scopes=["git:*"],
        conditions=[Condition("regex", r"git\s+push\s+--force.*\b(main|master)\b")],
        decision=RiskLevel.BLOCK,
        reason="Force push to protected branch",
        priority=100,
    ),

    # === REVIEW policies ===
    Policy(
        name="review_git_push",
        scopes=["git:push"],
        conditions=[Condition("keyword", "git push")],
        decision=RiskLevel.REVIEW_REQUIRED,
        reason="Git push requires review",
        priority=60,
    ),
    Policy(
        name="review_package_install",
        scopes=["shell:install"],
        conditions=[Condition("regex", r"(pip|npm|brew|apt|cargo)\s+install")],
        decision=RiskLevel.REVIEW_REQUIRED,
        reason="Package installation requires review",
        priority=55,
    ),
    Policy(
        name="review_network_access",
        scopes=["shell:network"],
        conditions=[Condition("regex", r"(curl|wget|fetch|http)")],
        decision=RiskLevel.REVIEW_REQUIRED,
        reason="Network access requires review",
        priority=50,
    ),
    Policy(
        name="review_docker",
        scopes=["shell:container"],
        conditions=[Condition("keyword", "docker")],
        decision=RiskLevel.REVIEW_REQUIRED,
        reason="Container operation requires review",
        priority=50,
    ),
    Policy(
        name="review_file_delete",
        scopes=["file:delete"],
        conditions=[Condition("regex", r"(rm\s|unlink|delete\s+file)")],
        decision=RiskLevel.REVIEW_REQUIRED,
        reason="File deletion requires review",
        priority=60,
    ),

    # === ALLOW policies (explicit allowlist) ===
    Policy(
        name="allow_readonly",
        scopes=["file:read", "search:*", "memory:read"],
        conditions=[Condition("regex", r"(read|search|grep|find|ls|cat|head)")],
        decision=RiskLevel.ALLOW,
        reason="Read-only operation",
        priority=40,
    ),

    # === Runaway detection ===
    Policy(
        name="block_runaway_agent",
        scopes=["*"],
        conditions=[Condition("consecutive_failures", "10")],
        decision=RiskLevel.BLOCK,
        reason="Agent appears to be in a failure loop (10+ consecutive failures)",
        priority=90,
    ),
]


class PolicyEngine:
    """
    Evaluates actions against a set of governance policies.

    Usage:
        engine = PolicyEngine()
        decision = engine.evaluate("git push --force origin main", agent_id="cursor")
        if decision.is_blocked:
            print(f"BLOCKED: {decision.reason}")
    """

    def __init__(self, policies: list[Policy] | None = None):
        self.policies = policies or list(BUILTIN_POLICIES)
        self._load_legacy_keywords()

    def _load_legacy_keywords(self) -> None:
        """Load keywords from existing policy.yaml for backward compatibility."""
        if not POLICY_FILE.exists():
            return

        blocked_kw: list[str] = []
        review_kw: list[str] = []
        section = None

        for line in POLICY_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped == "blocked_keywords:":
                section = "blocked"
                continue
            elif stripped == "review_keywords:":
                section = "review"
                continue
            elif stripped.endswith(":") and not stripped.startswith("-"):
                section = None
                continue

            if section and stripped.startswith("- "):
                kw = stripped[2:].strip()
                if section == "blocked":
                    blocked_kw.append(kw)
                elif section == "review":
                    review_kw.append(kw)

        for kw in blocked_kw:
            if not any(kw in str(c.value) for p in self.policies for c in p.conditions):
                self.policies.append(Policy(
                    name=f"legacy_block_{kw.replace(' ', '_')}",
                    scopes=["*"],
                    conditions=[Condition("keyword", kw)],
                    decision=RiskLevel.BLOCK,
                    reason=f"Blocked by legacy policy: {kw}",
                    priority=70,
                ))

        for kw in review_kw:
            if not any(kw in str(c.value) for p in self.policies for c in p.conditions):
                self.policies.append(Policy(
                    name=f"legacy_review_{kw.replace(' ', '_')}",
                    scopes=["*"],
                    conditions=[Condition("keyword", kw)],
                    decision=RiskLevel.REVIEW_REQUIRED,
                    reason=f"Review required by legacy policy: {kw}",
                    priority=45,
                ))

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self.policies.append(policy)

    def evaluate(
        self,
        action: str,
        agent_id: str = "unknown",
        scopes: list[str] | None = None,
        resource: str = "",
        route: str = "",
        recent_failures: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        """
        Evaluate an action against all policies.

        Returns the highest-risk matching decision.
        """
        context = EvalContext(
            action=action,
            agent_id=agent_id,
            scopes=scopes or [],
            resource=resource,
            route=route,
            recent_failures=recent_failures,
            metadata=metadata or {},
        )

        matched: list[Policy] = []
        for policy in self.policies:
            if policy.evaluate(context):
                matched.append(policy)

        if not matched:
            return PolicyDecision(
                risk=RiskLevel.ALLOW,
                matched_policies=[],
                action=action,
                reason="No policy matched — default ALLOW",
            )

        matched.sort(key=lambda p: (p.decision.value, p.priority), reverse=True)
        winning = matched[0]

        return PolicyDecision(
            risk=winning.decision,
            matched_policies=matched,
            action=action,
            reason=winning.reason,
            context={
                "agent_id": agent_id,
                "route": route,
                "matched_count": len(matched),
                "winning_policy": winning.name,
                "winning_priority": winning.priority,
            },
        )

    def classify_action(self, action: str, route_name: str | None = None) -> dict[str, Any]:
        """Backward-compatible interface matching guardian_check.classify_action()."""
        decision = self.evaluate(action, route=route_name or "")
        return {
            "risk": decision.risk.name,
            "matched": [p.name for p in decision.matched_policies],
            "action": action,
            "reason": decision.reason,
            "boundary_level": route_name or "OBSERVE_ONLY",
        }

    def list_policies(self) -> list[dict[str, Any]]:
        """List all active policies."""
        return [p.to_dict() for p in self.policies if p.enabled]

    def stats(self) -> dict[str, Any]:
        """Policy engine statistics."""
        by_decision = {"ALLOW": 0, "REVIEW_REQUIRED": 0, "BLOCK": 0}
        for p in self.policies:
            if p.enabled:
                by_decision[p.decision.name] += 1
        return {
            "total_policies": len(self.policies),
            "enabled": sum(1 for p in self.policies if p.enabled),
            "by_decision": by_decision,
        }
