"""Subsystem hooks for registering canonical truth nodes."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from kernel.truth.truth_graph import TruthGraph
from kernel.truth.truth_node import Mutability, TruthNode
from kernel.truth.truth_validator import ValidationResult


class SubsystemDomain(str, Enum):
    """Known subsystem domains for truth registration."""

    MEMORY = "memory"
    GOVERNANCE = "governance"
    RUNTIME = "runtime"
    TELEMETRY = "telemetry"
    IDENTITY = "identity"
    SYSTEM_STATE = "system_state"


class TruthRegistry:
    """
    Registry hooks for subsystems to publish auditable truth nodes.

    Each hook requires full provenance on registration.
    """

    def __init__(
        self,
        graph: TruthGraph | None = None,
        registry_guard: Any | None = None,
    ) -> None:
        self.graph = graph or TruthGraph()
        self._hooks: dict[SubsystemDomain, list[Callable[[TruthNode], None]]] = {}
        self._registry_guard = registry_guard
        if self._registry_guard is None:
            try:
                from kernel.isolation.registry_guard import RegistryGuard
                from kernel.isolation.write_target import WriteTarget

                guard = RegistryGuard()
                guard.bind("truth_registry", write_target=WriteTarget.TRUTH_GRAPH, owner="kernel")
                self._registry_guard = guard
            except ImportError:
                self._registry_guard = None

    def register_hook(
        self,
        domain: SubsystemDomain,
        callback: Callable[[TruthNode], None],
    ) -> None:
        self._hooks.setdefault(domain, []).append(callback)

    def _notify(self, domain: SubsystemDomain, node: TruthNode) -> None:
        for callback in self._hooks.get(domain, []):
            try:
                callback(node)
            except Exception:
                pass  # hooks are observational; must not block registration

    def register(
        self,
        domain: SubsystemDomain,
        *,
        node_id: str,
        source: str,
        owner: str,
        version: str,
        mutability: Mutability,
        payload: dict[str, Any] | None = None,
        execution_context: Any | None = None,
    ) -> ValidationResult:
        """Register a subsystem truth node under a domain namespace."""
        def _register() -> ValidationResult:
            namespaced_id = f"{domain.value}:{node_id}"
            node = TruthNode.create(
                node_id=namespaced_id,
                source=source,
                owner=owner,
                version=version,
                mutability=mutability,
                payload=payload or {},
            )
            result = self.graph.register_node(node)
            if result.valid:
                self._notify(domain, node)
            return result

        if execution_context is not None and self._registry_guard is not None:
            return self._registry_guard.mutate(
                "truth_registry",
                _register,
                context=execution_context,
                operation="register",
            )
        return _register()

    def register_memory(
        self,
        node_id: str,
        owner: str,
        version: str,
        payload: dict[str, Any],
        *,
        source: str = "memory.kernel",
        mutability: Mutability = Mutability.VERSIONED,
    ) -> ValidationResult:
        return self.register(
            SubsystemDomain.MEMORY,
            node_id=node_id,
            source=source,
            owner=owner,
            version=version,
            mutability=mutability,
            payload=payload,
        )

    def register_governance(
        self,
        node_id: str,
        owner: str,
        version: str,
        payload: dict[str, Any],
        *,
        source: str = "governance.audit_log",
        mutability: Mutability = Mutability.IMMUTABLE,
    ) -> ValidationResult:
        return self.register(
            SubsystemDomain.GOVERNANCE,
            node_id=node_id,
            source=source,
            owner=owner,
            version=version,
            mutability=mutability,
            payload=payload,
        )

    def register_runtime(
        self,
        node_id: str,
        owner: str,
        version: str,
        payload: dict[str, Any],
        *,
        source: str = "runtime.task_graph",
    ) -> ValidationResult:
        return self.register(
            SubsystemDomain.RUNTIME,
            node_id=node_id,
            source=source,
            owner=owner,
            version=version,
            mutability=Mutability.VERSIONED,
            payload=payload,
        )

    def register_telemetry(
        self,
        node_id: str,
        owner: str,
        version: str,
        payload: dict[str, Any],
        *,
        source: str = "observability.telemetry",
    ) -> ValidationResult:
        return self.register(
            SubsystemDomain.TELEMETRY,
            node_id=node_id,
            source=source,
            owner=owner,
            version=version,
            mutability=Mutability.MUTABLE,
            payload=payload,
        )

    def register_identity(
        self,
        node_id: str,
        owner: str,
        version: str,
        payload: dict[str, Any],
        *,
        source: str = "identity.self_model",
    ) -> ValidationResult:
        return self.register(
            SubsystemDomain.IDENTITY,
            node_id=node_id,
            source=source,
            owner=owner,
            version=version,
            mutability=Mutability.VERSIONED,
            payload=payload,
        )

    def register_system_state(
        self,
        node_id: str,
        owner: str,
        version: str,
        payload: dict[str, Any],
        *,
        source: str = "state.system_state",
    ) -> ValidationResult:
        return self.register(
            SubsystemDomain.SYSTEM_STATE,
            node_id=node_id,
            source=source,
            owner=owner,
            version=version,
            mutability=Mutability.MUTABLE,
            payload=payload,
        )

    def domains(self) -> list[str]:
        return [d.value for d in SubsystemDomain]
