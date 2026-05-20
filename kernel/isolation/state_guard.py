"""State guard — enforces write_targets and prevents cross-context writes."""

from __future__ import annotations

from dataclasses import dataclass

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope


@dataclass
class WriteDenial:
    target: str
    context_id: str
    reason: str


class StateGuard:
    """
    Validates state mutations against execution context write_targets.

    No cross-context writes: active scope must match the writing context.
    """

    def __init__(self, scope: ExecutionScope | None = None) -> None:
        self.scope = scope or ExecutionScope()
        self._denials: list[WriteDenial] = []

    @property
    def denials(self) -> list[WriteDenial]:
        return list(self._denials)

    def check_write(self, context: ExecutionContext, target: str) -> bool:
        active = self.scope.current()
        if active is not None and active.context_id != context.context_id:
            self._deny(target, context.context_id, "cross-context write blocked")
            return False
        if not context.has_permission(Permission.WRITE):
            self._deny(target, context.context_id, "WRITE permission not granted")
            return False
        if not context.can_write(target):
            self._deny(target, context.context_id, f"target '{target}' not in write_targets")
            return False
        return True

    def assert_write(self, context: ExecutionContext, target: str) -> None:
        if not self.check_write(context, target):
            raise PermissionError(
                f"Write to '{target}' denied for context {context.context_id}"
            )

    def _deny(self, target: str, context_id: str, reason: str) -> None:
        self._denials.append(WriteDenial(target=target, context_id=context_id, reason=reason))
