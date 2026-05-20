"""Resource guard — enforces allowed_resources within an execution context."""

from __future__ import annotations

from dataclasses import dataclass

from kernel.isolation.execution_context import ExecutionContext


@dataclass
class ResourceDenial:
    resource: str
    context_id: str
    reason: str


class ResourceGuard:
    """Validates resource access against ExecutionContext.allowed_resources."""

    def __init__(self) -> None:
        self._denials: list[ResourceDenial] = []

    @property
    def denials(self) -> list[ResourceDenial]:
        return list(self._denials)

    def check(self, context: ExecutionContext, resource: str) -> bool:
        if context.can_access(resource):
            return True
        self._denials.append(
            ResourceDenial(
                resource=resource,
                context_id=context.context_id,
                reason=f"resource '{resource}' not in allowed_resources",
            )
        )
        return False

    def assert_allowed(self, context: ExecutionContext, resource: str) -> None:
        if not self.check(context, resource):
            raise PermissionError(
                f"Resource '{resource}' denied for context {context.context_id}"
            )
