"""Registry guard — govern Skill/Patch/Truth registry mutations."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ExecutionScope, ScopeType
from kernel.isolation.registry_mutation import RegistryMutation
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget

T = TypeVar("T")


@dataclass
class RegistryBinding:
    name: str
    write_target: WriteTarget
    owner: str
    registered_at: float = field(default_factory=time.time)


class RegistryGuard:
    """Require ExecutionContext for registry register/deregister operations."""

    def __init__(
        self,
        scope: ExecutionScope | None = None,
        write_guard: WriteGuard | None = None,
        *,
        authority_trace: Any | None = None,
        require_context: bool = False,
    ) -> None:
        self._scope = scope or ExecutionScope()
        self._write_guard = write_guard or WriteGuard(scope=self._scope)
        self._bindings: dict[str, RegistryBinding] = {}
        self._mutations: list[RegistryMutation] = []
        self._authority_trace = authority_trace
        self._require_context = require_context

    def bind(
        self,
        name: str,
        *,
        write_target: WriteTarget,
        owner: str,
    ) -> RegistryBinding:
        binding = RegistryBinding(name=name, write_target=write_target, owner=owner)
        self._bindings[name] = binding
        return binding

    def mutate(
        self,
        registry_name: str,
        fn: Callable[[], T],
        *,
        context: ExecutionContext | None = None,
        operation: str = "register",
    ) -> T:
        binding = self._bindings.get(registry_name)
        if binding is None:
            raise KeyError(f"registry '{registry_name}' not bound to RegistryGuard")

        ctx = context or self._scope.current()
        if ctx is None and self._require_context:
            raise PermissionError(
                f"registry '{registry_name}' requires ExecutionContext when guard is active"
            )
        if ctx is None:
            ctx = ExecutionContext.create(
                caller_id=f"registry:{registry_name}",
                caller_type="kernel",
                scope=ScopeType.GOVERNED_WRITE.value,
                permissions={Permission.READ, Permission.WRITE},
                allowed_write_targets={binding.write_target.value},
                rollback_plan=RollbackPlan(rollback_type=RollbackType.LOGICAL),
            )
            self._scope.enter(ctx)
            try:
                return self._execute(binding, registry_name, fn, ctx, operation)
            finally:
                self._scope.exit(ctx.context_id)
        return self._execute(binding, registry_name, fn, ctx, operation)

    def _execute(
        self,
        binding: RegistryBinding,
        registry_name: str,
        fn: Callable[[], T],
        ctx: ExecutionContext,
        operation: str,
    ) -> T:
        self._write_guard.assert_write(binding.write_target, context=ctx)
        result = fn()
        self._mutations.append(
            RegistryMutation(
                registry=registry_name,
                operation=operation,
                write_target=binding.write_target.value,
                context_id=ctx.context_id,
                caller_id=ctx.caller_id,
            )
        )
        if self._authority_trace and hasattr(
            self._authority_trace, "record_guarded_operation"
        ):
            self._authority_trace.record_guarded_operation(
                mutation_type="REGISTRY_MUTATION",
                target=registry_name,
                context_id=ctx.context_id,
                caller_id=ctx.caller_id,
                rollback_type=(
                    ctx.rollback_plan.rollback_type.value
                    if ctx.rollback_plan
                    else None
                ),
                result="ok",
                detail=f"{operation}:{binding.write_target.value}",
            )
        return result

    def stats(self) -> dict[str, Any]:
        return {
            "bindings": len(self._bindings),
            "mutations": len(self._mutations),
        }
