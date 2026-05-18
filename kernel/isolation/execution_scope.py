"""Execution scope — active context registry and cross-context enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.isolation.execution_context import ExecutionContext


class ScopeType(str, Enum):
    """Execution scope classification (v0.4.3)."""

    READ_ONLY = "read_only"
    SANDBOX = "sandbox"
    LOCAL_STATE = "local_state"
    GOVERNED_WRITE = "governed_write"
    EXTERNAL_ACTION = "external_action"
    RELEASE_OPERATION = "release_operation"


@dataclass
class ScopeViolation:
    code: str
    message: str
    context_id: str | None = None


class ExecutionScope:
    """
    Manages active execution contexts (stack).

    Enforces: no execution without context; no cross-context writes.
    """

    def __init__(self) -> None:
        self._stack: list[str] = []
        self._active: dict[str, ExecutionContext] = {}
        self._violations: list[ScopeViolation] = []

    @property
    def violations(self) -> list[ScopeViolation]:
        return list(self._violations)

    def enter(self, context: ExecutionContext) -> None:
        self._active[context.context_id] = context
        self._stack.append(context.context_id)

    def exit(self, context_id: str) -> ExecutionContext | None:
        ctx = self._active.pop(context_id, None)
        if context_id in self._stack:
            self._stack = [cid for cid in self._stack if cid != context_id]
        return ctx

    def current(self) -> ExecutionContext | None:
        while self._stack:
            top = self._stack[-1]
            ctx = self._active.get(top)
            if ctx is not None:
                return ctx
            self._stack.pop()
        return None

    def require_context(self) -> ExecutionContext:
        ctx = self.current()
        if ctx is None:
            violation = ScopeViolation(
                code="no_context",
                message="execution attempted without ExecutionContext",
            )
            self._violations.append(violation)
            raise RuntimeError(violation.message)
        return ctx

    def assert_same_scope(self, other: ExecutionContext) -> bool:
        current = self.current()
        if current is None:
            self._record_violation("no_context", "cross-context check without active context")
            return False
        if current.scope != other.scope:
            self._record_violation(
                "cross_scope_write",
                f"write from scope '{current.scope}' to '{other.scope}' blocked",
                current.context_id,
            )
            return False
        return True

    def scope_type(self) -> ScopeType | None:
        ctx = self.current()
        if ctx is None:
            return None
        try:
            return ScopeType(ctx.scope)
        except ValueError:
            return None

    def _record_violation(self, code: str, message: str, context_id: str | None = None) -> None:
        self._violations.append(
            ScopeViolation(code=code, message=message, context_id=context_id)
        )

    def stats(self) -> dict[str, Any]:
        return {
            "active_contexts": len(self._active),
            "stack_depth": len(self._stack),
            "violation_count": len(self._violations),
        }
