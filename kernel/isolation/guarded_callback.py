"""Guarded callback — thin facade over CallbackGuard for bus/somatic registration."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from kernel.isolation.callback_guard import CallbackGuard
from kernel.isolation.callback_scope import CallbackScope, ContextInheritance
from kernel.isolation.execution_scope import ExecutionScope
from kernel.isolation.write_guard import WriteGuard

F = TypeVar("F", bound=Callable[..., Any])


class GuardedCallback:
    """
    Opt-in wrapper aligning IntegrationBus.register_guarded_callback with v0.4.4 trace.

    Does not alter existing unguarded hooks.
    """

    def __init__(
        self,
        callback_guard: CallbackGuard | None = None,
        *,
        authority_trace: Any | None = None,
    ) -> None:
        scope = ExecutionScope()
        self._guard = callback_guard or CallbackGuard(
            execution_scope=scope,
            write_guard=WriteGuard(scope=scope),
        )
        self.authority_trace = authority_trace

    def register(
        self,
        name: str,
        fn: F,
        *,
        source: str,
        allowed_writes: frozenset[str] | None = None,
        max_duration_seconds: float = 30.0,
        inheritance: ContextInheritance = ContextInheritance.INHERIT,
    ) -> F:
        scope = CallbackScope(
            source=source or name,
            allowed_writes=allowed_writes or frozenset(),
            max_duration_seconds=max_duration_seconds,
            inheritance=inheritance,
        )
        wrapped = self._guard.wrap(name, fn, callback_scope=scope)
        if self.authority_trace and hasattr(self.authority_trace, "record_guarded_operation"):
            self.authority_trace.record_guarded_operation(
                mutation_type="CALLBACK_MUTATION",
                target=name,
                caller_id=source,
                result="registered",
            )
        return wrapped  # type: ignore[return-value]

    @property
    def guard(self) -> CallbackGuard:
        return self._guard
