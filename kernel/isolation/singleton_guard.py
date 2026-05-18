"""Singleton guard — register singletons; require context for mutation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.execution_scope import ExecutionScope
from kernel.isolation.singleton_mutation import SingletonMutation

T = TypeVar("T")


@dataclass
class RegisteredSingleton:
    name: str
    owner: str
    registered_at: float = field(default_factory=time.time)


class SingletonGuard:
    """Tracks singleton identities and gates in-place mutations."""

    def __init__(self, scope: ExecutionScope | None = None) -> None:
        self._scope = scope or ExecutionScope()
        self._registry: dict[str, RegisteredSingleton] = {}
        self._mutations: list[SingletonMutation] = []

    def register(self, name: str, *, owner: str) -> RegisteredSingleton:
        entry = RegisteredSingleton(name=name, owner=owner)
        self._registry[name] = entry
        return entry

    def mutate(
        self,
        name: str,
        fn: Callable[[], T],
        *,
        context: ExecutionContext | None = None,
        attribute: str | None = None,
    ) -> T:
        if name not in self._registry:
            self.register(name, owner="unknown")

        ctx = context or self._scope.current()
        if ctx is None:
            raise PermissionError(f"singleton '{name}' mutation requires ExecutionContext")

        mutation = SingletonMutation(
            singleton=name,
            attribute=attribute,
            context_id=ctx.context_id,
            caller_id=ctx.caller_id,
        )
        self._mutations.append(mutation)
        return fn()

    def stats(self) -> dict[str, Any]:
        return {
            "registered": len(self._registry),
            "mutations": len(self._mutations),
        }
