"""Callback guard — register and wrap bus/somatic callbacks."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from kernel.isolation.callback_scope import CallbackScope, ContextInheritance
from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope
from kernel.isolation.write_guard import WriteGuard

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class RegisteredCallback:
    name: str
    scope: CallbackScope
    registered_at: float = field(default_factory=time.time)


class CallbackGuard:
    """Register callbacks with source, allowed reads/writes, max duration."""

    def __init__(
        self,
        execution_scope: ExecutionScope | None = None,
        write_guard: WriteGuard | None = None,
    ) -> None:
        self._scope = execution_scope or ExecutionScope()
        self._write_guard = write_guard or WriteGuard(scope=self._scope)
        self._registry: dict[str, RegisteredCallback] = {}
        self._contained: int = 0
        self._violations: list[str] = []

    @property
    def violations(self) -> list[str]:
        return list(self._violations)

    def register(self, name: str, callback_scope: CallbackScope) -> RegisteredCallback:
        entry = RegisteredCallback(name=name, scope=callback_scope)
        self._registry[name] = entry
        return entry

    def wrap(
        self,
        name: str,
        fn: F,
        *,
        callback_scope: CallbackScope | None = None,
    ) -> F:
        if callback_scope is None:
            callback_scope = CallbackScope(source=name)
        if name not in self._registry:
            self.register(name, callback_scope)

        async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self._invoke(name, fn, args, kwargs, is_async=True)

        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._invoke_sync(name, fn, args, kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(fn):
            return _async_wrapper  # type: ignore[return-value]
        return _sync_wrapper  # type: ignore[return-value]

    def _invoke_sync(self, name: str, fn: Callable, args: tuple, kwargs: dict) -> Any:
        reg = self._registry[name]
        started = time.time()
        ctx = self._resolve_context(reg.scope)
        token = None
        if ctx is not None:
            self._scope.enter(ctx)
        try:
            if time.time() - started > reg.scope.max_duration_seconds:
                raise TimeoutError(f"callback '{name}' exceeded max duration")
            self._contained += 1
            return fn(*args, **kwargs)
        finally:
            if ctx is not None and token is None:
                self._scope.exit(ctx.context_id)

    async def _invoke(
        self,
        name: str,
        fn: Callable,
        args: tuple,
        kwargs: dict,
        *,
        is_async: bool,
    ) -> Any:
        reg = self._registry[name]
        started = time.time()
        ctx = self._resolve_context(reg.scope)
        if ctx is not None:
            self._scope.enter(ctx)
        try:
            if time.time() - started > reg.scope.max_duration_seconds:
                raise TimeoutError(f"callback '{name}' exceeded max duration")
            self._contained += 1
            result = fn(*args, **kwargs)
            if is_async:
                import asyncio

                if asyncio.iscoroutine(result):
                    return await result
            return result
        finally:
            if ctx is not None:
                self._scope.exit(ctx.context_id)

    def _resolve_context(self, cb_scope: CallbackScope) -> ExecutionContext | None:
        parent = self._scope.current()
        if cb_scope.inheritance == ContextInheritance.ISOLATE:
            return ExecutionContext.create(
                caller_id=f"callback:{cb_scope.source}",
                caller_type="callback",
                scope="sandbox",
                permissions={Permission.READ, Permission.WRITE},
                allowed_write_targets=set(cb_scope.allowed_writes),
                metadata={"sandbox": True},
            )
        return parent

    def stats(self) -> dict[str, Any]:
        return {
            "registered": len(self._registry),
            "contained_invocations": self._contained,
            "violations": len(self._violations),
        }
