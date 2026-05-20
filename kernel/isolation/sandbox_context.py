"""Sandbox context — isolated execution that cannot touch production stores."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator, Iterator

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope, ScopeType
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.sandbox_memory import SandboxMemory
from kernel.isolation.write_target import WriteTarget


@dataclass
class SandboxContext:
    """
    Sandboxed execution envelope.

    Writes never hit production memory/governance/truth unless explicitly
    marked non-sandbox via metadata['sandbox']=False.
    """

    scope: ExecutionScope = field(default_factory=ExecutionScope)
    memory: SandboxMemory = field(default_factory=SandboxMemory)
    _active: ExecutionContext | None = None

    def build_context(self, caller_id: str = "sandbox") -> ExecutionContext:
        return ExecutionContext.create(
            caller_id=caller_id,
            caller_type="system",
            scope=ScopeType.SANDBOX.value,
            permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
            allowed_write_targets={WriteTarget.STATE.value, "sandbox"},
            rollback_plan=RollbackPlan(rollback_type=RollbackType.SNAPSHOT),
            metadata={"sandbox": True},
        )

    @contextmanager
    def activate(self, caller_id: str = "sandbox") -> Generator[ExecutionContext, None, None]:
        ctx = self.build_context(caller_id)
        self._active = ctx
        self.scope.enter(ctx)
        try:
            yield ctx
        finally:
            self.scope.exit(ctx.context_id)
            self._active = None

    def is_sandboxed_target(self, target: str) -> bool:
        production = {
            WriteTarget.MEMORY.value,
            WriteTarget.GOVERNANCE_AUDIT.value,
            WriteTarget.TRUTH_GRAPH.value,
        }
        return target in production

    def block_production_write(self, target: str, *, context: ExecutionContext | None = None) -> bool:
        ctx = context or self._active
        if ctx is None:
            return False
        if not ctx.metadata.get("sandbox", False):
            return False
        if self.is_sandboxed_target(target):
            return True
        return False

    def stats(self) -> dict[str, Any]:
        return {
            "active": self._active is not None,
            "memory_entries": len(self.memory.entries),
        }
