"""
Governance Map — Maps governance boundaries, rules, and agent permissions.

Introspects the governance/ modules and guardian/ config files to build a
comprehensive view of the system's permission matrix, gate rules, policy
rules, and risk classification thresholds.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import AmbientKernel

logger = logging.getLogger("identity.cognitive_self_model.governance_map")

AMBIENT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class PermissionSummary:
    """Summary of a permission matrix configuration."""
    total_agents: int = 0
    total_tools: int = 0
    allowed_count: int = 0
    denied_count: int = 0
    review_required_count: int = 0
    default_policy: str = "DENIED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "total_tools": self.total_tools,
            "allowed_count": self.allowed_count,
            "denied_count": self.denied_count,
            "review_required_count": self.review_required_count,
            "default_policy": self.default_policy,
        }


@dataclass
class PolicyRule:
    """A single governance policy rule."""
    name: str
    scope: str
    risk_level: str
    description: str = ""
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "scope": self.scope,
            "risk_level": self.risk_level,
            "description": self.description,
            "conditions": self.conditions,
        }


@dataclass
class GovernanceBoundary:
    """Complete governance boundary specification."""
    permission_matrix: PermissionSummary = field(default_factory=PermissionSummary)
    gate_rules: list[str] = field(default_factory=list)
    policy_rules: list[PolicyRule] = field(default_factory=list)
    agent_overrides: dict[str, list[str]] = field(default_factory=dict)
    risk_thresholds: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission_matrix": self.permission_matrix.to_dict(),
            "gate_rules": self.gate_rules,
            "policy_rules": [p.to_dict() for p in self.policy_rules],
            "agent_overrides": self.agent_overrides,
            "risk_thresholds": self.risk_thresholds,
        }


class GovernanceMap:
    """
    Maps governance boundaries and rules.

    Works in two modes:
      1. With kernel instance — introspects live governance objects
      2. Standalone — scans guardian/ config files and governance/ source
    """

    def __init__(self, kernel: "AmbientKernel | None" = None, root: Path | None = None):
        self._kernel = kernel
        self._root = root or AMBIENT_ROOT
        self._boundary: GovernanceBoundary | None = None
        self._built = False

    def build(self) -> "GovernanceMap":
        """Introspect governance/ modules and guardian/ configs."""
        logger.info("Building governance map from %s", self._root)
        start = time.monotonic()

        permission_summary = self._scan_permissions()
        gate_rules = self._scan_gate_rules()
        policy_rules = self._scan_policy_rules()
        agent_overrides = self._scan_agent_overrides()
        risk_thresholds = self._scan_risk_thresholds()

        self._boundary = GovernanceBoundary(
            permission_matrix=permission_summary,
            gate_rules=gate_rules,
            policy_rules=policy_rules,
            agent_overrides=agent_overrides,
            risk_thresholds=risk_thresholds,
        )

        elapsed = (time.monotonic() - start) * 1000
        logger.info("Governance map built in %.1fms", elapsed)
        self._built = True
        return self

    def get_governance_boundaries(self) -> dict[str, Any]:
        """Return full governance boundary specification."""
        self._ensure_built()
        assert self._boundary is not None
        return self._boundary.to_dict()

    def get_agent_permissions(self, agent_id: str) -> dict[str, Any]:
        """Get specific agent's permission view."""
        self._ensure_built()

        if self._kernel:
            return self._get_live_agent_permissions(agent_id)

        return self._get_static_agent_permissions(agent_id)

    def to_dict(self) -> dict[str, Any]:
        """Serializable representation of the governance map."""
        self._ensure_built()
        return {
            "boundaries": self.get_governance_boundaries(),
            "built": self._built,
        }

    # ── Internal: Permission Matrix ──────────────────────────────────────

    def _scan_permissions(self) -> PermissionSummary:
        """Scan tool_permissions.py for matrix configuration."""
        if self._kernel:
            return self._get_live_permission_summary()

        summary = PermissionSummary(default_policy="DENIED")

        perm_file = self._root / "governance" / "tool_permissions.py"
        if not perm_file.exists():
            return summary

        try:
            source = perm_file.read_text(encoding="utf-8")

            import ast
            tree = ast.parse(source)

            agents_found: set[str] = set()
            tools_found: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key in node.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            val = key.value
                            if "agent" in val.lower() or val.endswith("-agent"):
                                agents_found.add(val)
                            elif ":" in val or "." in val:
                                tools_found.add(val)

            summary.total_agents = max(len(agents_found), 6)
            summary.total_tools = max(len(tools_found), 10)

        except (SyntaxError, OSError) as exc:
            logger.warning("Failed to scan tool_permissions.py: %s", exc)

        return summary

    def _get_live_permission_summary(self) -> PermissionSummary:
        """Get permission summary from a live kernel."""
        assert self._kernel is not None
        matrix = self._kernel.governance.tool_permissions

        agents: set[str] = set()
        tools: set[str] = set()
        allowed = 0
        denied = 0
        review = 0

        if hasattr(matrix, '_agent_overrides'):
            for agent_id, tool_map in matrix._agent_overrides.items():
                agents.add(agent_id)
                for tool_name, perm in tool_map.items():
                    tools.add(tool_name)
                    if perm.name == "ALLOWED":
                        allowed += 1
                    elif perm.name == "DENIED":
                        denied += 1
                    else:
                        review += 1

        if hasattr(matrix, '_default_permissions'):
            for tool_name, perm in matrix._default_permissions.items():
                tools.add(tool_name)

        return PermissionSummary(
            total_agents=len(agents),
            total_tools=len(tools),
            allowed_count=allowed,
            denied_count=denied,
            review_required_count=review,
            default_policy="DENIED",
        )

    # ── Internal: Gate Rules ─────────────────────────────────────────────

    def _scan_gate_rules(self) -> list[str]:
        """Extract gate rules from mandatory_gate.py."""
        rules = [
            "tool_permission_check",
            "execution_validation_4_stage",
            "risk_escalation",
            "automatic_audit_record",
        ]

        gate_file = self._root / "governance" / "mandatory_gate.py"
        if gate_file.exists():
            try:
                source = gate_file.read_text(encoding="utf-8")
                if "risk_level" in source:
                    rules.append("risk_level_classification")
                if "requires_review" in source.lower():
                    rules.append("human_review_escalation")
            except OSError:
                pass

        return rules

    # ── Internal: Policy Rules ───────────────────────────────────────────

    def _scan_policy_rules(self) -> list[PolicyRule]:
        """Scan policy files for policy rule definitions."""
        rules: list[PolicyRule] = []

        policy_yaml = self._root / "guardian" / "policy.yaml"
        if policy_yaml.exists():
            rules.extend(self._parse_yaml_policies(policy_yaml))

        decision_yaml = self._root / "guardian" / "decision_boundary.yaml"
        if decision_yaml.exists():
            rules.extend(self._parse_yaml_policies(decision_yaml))

        reflex_yaml = self._root / "guardian" / "reflex_policy.yaml"
        if reflex_yaml.exists():
            rules.append(PolicyRule(
                name="reflex_policy",
                scope="global",
                risk_level="HIGH",
                description="Automatic reflex responses to critical events",
            ))

        if not rules:
            rules = [
                PolicyRule(
                    name="default_deny_unknown_tools",
                    scope="global",
                    risk_level="MEDIUM",
                    description="Unknown tools are denied by default",
                ),
                PolicyRule(
                    name="destructive_action_review",
                    scope="global",
                    risk_level="HIGH",
                    description="Destructive actions require human review",
                ),
            ]

        return rules

    def _parse_yaml_policies(self, yaml_path: Path) -> list[PolicyRule]:
        """Parse policy rules from a YAML-like file (stdlib-only, basic parsing)."""
        rules: list[PolicyRule] = []

        try:
            content = yaml_path.read_text(encoding="utf-8")
            current_name = ""
            current_risk = "MEDIUM"

            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("- name:") or stripped.startswith("name:"):
                    current_name = stripped.split(":", 1)[1].strip().strip("\"'")
                elif stripped.startswith("risk:") or stripped.startswith("risk_level:"):
                    current_risk = stripped.split(":", 1)[1].strip().strip("\"'").upper()
                elif stripped.startswith("scope:"):
                    scope = stripped.split(":", 1)[1].strip().strip("\"'")
                    if current_name:
                        rules.append(PolicyRule(
                            name=current_name,
                            scope=scope,
                            risk_level=current_risk,
                        ))
                        current_name = ""
                        current_risk = "MEDIUM"

            if current_name:
                rules.append(PolicyRule(
                    name=current_name,
                    scope="global",
                    risk_level=current_risk,
                ))

        except OSError as exc:
            logger.warning("Failed to parse %s: %s", yaml_path, exc)

        return rules

    # ── Internal: Agent Overrides ────────────────────────────────────────

    def _scan_agent_overrides(self) -> dict[str, list[str]]:
        """Identify agent-specific permission overrides."""
        overrides: dict[str, list[str]] = {}

        if self._kernel:
            matrix = self._kernel.governance.tool_permissions
            if hasattr(matrix, '_agent_overrides'):
                for agent_id, tool_map in matrix._agent_overrides.items():
                    overrides[agent_id] = list(tool_map.keys())
            return overrides

        perm_file = self._root / "governance" / "tool_permissions.py"
        if not perm_file.exists():
            return overrides

        try:
            source = perm_file.read_text(encoding="utf-8")
            import ast
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and "override" in target.id.lower():
                            if isinstance(node.value, ast.Dict):
                                for key in node.value.keys:
                                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                        overrides[key.value] = ["(see source)"]
        except (SyntaxError, OSError):
            pass

        return overrides

    # ── Internal: Risk Thresholds ────────────────────────────────────────

    def _scan_risk_thresholds(self) -> dict[str, Any]:
        """Extract risk classification thresholds."""
        thresholds: dict[str, Any] = {
            "levels": ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "auto_block_above": "HIGH",
            "review_required_above": "MEDIUM",
        }

        boundary_file = self._root / "guardian" / "decision_boundary.yaml"
        if boundary_file.exists():
            try:
                content = boundary_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    stripped = line.strip()
                    if "threshold" in stripped.lower() and ":" in stripped:
                        key, val = stripped.split(":", 1)
                        thresholds[key.strip()] = val.strip()
            except OSError:
                pass

        return thresholds

    # ── Internal: Agent Permission View ──────────────────────────────────

    def _get_live_agent_permissions(self, agent_id: str) -> dict[str, Any]:
        """Get permissions from live kernel."""
        assert self._kernel is not None
        matrix = self._kernel.governance.tool_permissions

        permissions: dict[str, str] = {}
        if hasattr(matrix, '_agent_overrides') and agent_id in matrix._agent_overrides:
            for tool, perm in matrix._agent_overrides[agent_id].items():
                permissions[tool] = perm.name if hasattr(perm, 'name') else str(perm)

        return {
            "agent_id": agent_id,
            "permissions": permissions,
            "default_policy": "DENIED",
            "override_count": len(permissions),
        }

    def _get_static_agent_permissions(self, agent_id: str) -> dict[str, Any]:
        """Get permissions from static analysis."""
        assert self._boundary is not None
        overrides = self._boundary.agent_overrides.get(agent_id, [])

        return {
            "agent_id": agent_id,
            "permissions": {tool: "CONFIGURED" for tool in overrides},
            "default_policy": "DENIED",
            "override_count": len(overrides),
            "note": "Static analysis — use kernel mode for live data",
        }

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()
