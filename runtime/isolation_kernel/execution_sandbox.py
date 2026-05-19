"""
Execution Sandbox — Per-agent task execution with isolation enforcement.

Wraps any task executor with pre-execution boundary checks, governance gate
integration, memory write tracking, and post-execution auditing. Each sandbox
is scoped to a single agent and its IsolationPolicy.

SandboxManager is the entry point: it creates sandboxes on demand using the
BoundaryRegistry and an optional MandatoryGate reference.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from runtime.isolation_kernel.boundary_definitions import (
    BoundaryRegistry,
    IsolationPolicy,
)

log = logging.getLogger(__name__)


@dataclass
class GateCheckResult:
    passed: bool
    risk_level: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "risk_level": self.risk_level,
            "reason": self.reason,
        }


@dataclass
class SandboxAuditRecord:
    agent_id: str
    task_summary: str
    started_at: str
    completed_at: str
    violations: list[str] = field(default_factory=list)
    memory_writes: int = 0
    governance_result: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_summary": self.task_summary,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "violations": self.violations,
            "memory_writes": self.memory_writes,
            "governance_result": self.governance_result,
        }


@dataclass
class SandboxResult:
    success: bool
    result: Any
    violations: list[str] = field(default_factory=list)
    write_count: int = 0
    tokens_used: int = 0
    audit: SandboxAuditRecord | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "violations": self.violations,
            "write_count": self.write_count,
            "tokens_used": self.tokens_used,
            "audit": self.audit.to_dict() if self.audit else None,
        }


class ExecutionSandbox:
    """Per-agent sandbox that wraps task execution with isolation enforcement."""

    def __init__(
        self,
        agent_id: str,
        policy: IsolationPolicy,
        gate: Any = None,
    ) -> None:
        self._agent_id = agent_id
        self._policy = policy
        self._gate = gate
        self._write_count = 0

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def policy(self) -> IsolationPolicy:
        return self._policy

    def execute_task(self, task: dict, executor: Callable) -> SandboxResult:
        started_at = datetime.now(timezone.utc).isoformat()
        violations = self._pre_execution_checks(task)

        if violations:
            log.warning(
                "Sandbox pre-check violations for %s: %s", self._agent_id, violations,
            )
            audit = self._post_execution_audit(None, 0, started_at, violations)
            return SandboxResult(
                success=False,
                result=None,
                violations=violations,
                write_count=0,
                tokens_used=0,
                audit=audit,
            )

        gate_result = self._enforce_governance(task)
        if gate_result and not gate_result.passed:
            violations.append(f"Governance gate blocked: {gate_result.reason}")
            audit = self._post_execution_audit(
                None, 0, started_at, violations, gate_result.risk_level,
            )
            return SandboxResult(
                success=False,
                result=None,
                violations=violations,
                write_count=0,
                tokens_used=0,
                audit=audit,
            )

        self._write_count = 0
        wrapped = self._wrap_memory_access(executor)

        try:
            result = wrapped(task)
            tokens_used = result.get("tokens_used", 0) if isinstance(result, dict) else 0
            audit = self._post_execution_audit(
                result, self._write_count, started_at, violations,
                gate_result.risk_level if gate_result else None,
            )
            return SandboxResult(
                success=True,
                result=result,
                violations=violations,
                write_count=self._write_count,
                tokens_used=tokens_used,
                audit=audit,
            )
        except Exception as exc:
            violations.append(f"Execution error: {exc}")
            audit = self._post_execution_audit(
                None, self._write_count, started_at, violations,
                gate_result.risk_level if gate_result else None,
            )
            return SandboxResult(
                success=False,
                result=None,
                violations=violations,
                write_count=self._write_count,
                tokens_used=0,
                audit=audit,
            )

    def _pre_execution_checks(self, task: dict) -> list[str]:
        violations: list[str] = []
        required_tools = task.get("required_tools", [])
        for tool in required_tools:
            for denied in self._policy.denied_tools:
                if tool == denied or (denied.endswith(":*") and tool.startswith(denied[:-1])):
                    violations.append(f"Task requires denied tool '{tool}'")

        target_layers = task.get("target_memory_layers", [])
        for layer in target_layers:
            if layer not in self._policy.allowed_memory_layers:
                violations.append(
                    f"Task targets disallowed memory layer '{layer}'"
                )
        return violations

    def _enforce_governance(self, task: dict) -> GateCheckResult | None:
        if self._gate is None:
            return None
        try:
            action = task.get("description", task.get("type", "unknown_task"))
            gate_result = self._gate.check(
                action=str(action),
                agent_id=self._agent_id,
                tool_name=task.get("tool_name"),
            )
            return GateCheckResult(
                passed=gate_result.allowed,
                risk_level=gate_result.risk_level.name
                if hasattr(gate_result.risk_level, "name")
                else str(gate_result.risk_level),
                reason=gate_result.reason,
            )
        except Exception as exc:
            log.error("Governance gate error for %s: %s", self._agent_id, exc)
            return GateCheckResult(
                passed=False,
                risk_level="ERROR",
                reason=f"Gate invocation failed: {exc}",
            )

    def _wrap_memory_access(self, executor: Callable) -> Callable:
        sandbox = self

        def wrapped(task: dict) -> Any:
            result = executor(task)
            if isinstance(result, dict):
                sandbox._write_count += result.get("memory_writes", 0)
            return result

        return wrapped

    def _post_execution_audit(
        self,
        result: Any,
        write_count: int,
        started_at: str,
        violations: list[str],
        governance_result: str | None = None,
    ) -> SandboxAuditRecord:
        completed_at = datetime.now(timezone.utc).isoformat()
        task_summary = ""
        if isinstance(result, dict):
            task_summary = result.get("summary", result.get("status", ""))[:200]
        return SandboxAuditRecord(
            agent_id=self._agent_id,
            task_summary=task_summary,
            started_at=started_at,
            completed_at=completed_at,
            violations=list(violations),
            memory_writes=write_count,
            governance_result=governance_result,
        )


class SandboxManager:
    """Factory and registry for per-agent execution sandboxes."""

    def __init__(
        self,
        registry: BoundaryRegistry,
        gate: Any = None,
    ) -> None:
        self._registry = registry
        self._gate = gate
        self._audit_log: list[SandboxAuditRecord] = []

    def create_sandbox(self, agent_id: str) -> ExecutionSandbox:
        policy = self._registry.get_policy(agent_id)
        return ExecutionSandbox(agent_id, policy, gate=self._gate)

    def execute_in_sandbox(
        self,
        agent_id: str,
        task: dict,
        executor: Callable,
    ) -> SandboxResult:
        sandbox = self.create_sandbox(agent_id)
        result = sandbox.execute_task(task, executor)
        if result.audit:
            self._record_audit(result.audit)
        return result

    def _record_audit(self, audit: SandboxAuditRecord) -> None:
        """Persist sandbox audit (governed path when GovernanceAuditLog available)."""
        self._audit_log.append(audit)
        try:
            from governance.audit_log import GovernanceAuditLog
            from governance.policy_engine import RiskLevel

            GovernanceAuditLog().record_decision(
                action=f"sandbox:{audit.task_summary[:200]}",
                risk=RiskLevel.ALLOW,
                reason="sandbox_execution_audit",
                agent_id=audit.agent_id,
                metadata=audit.to_dict(),
            )
        except Exception:
            pass

    def get_audit_log(self) -> list[SandboxAuditRecord]:
        return list(self._audit_log)
