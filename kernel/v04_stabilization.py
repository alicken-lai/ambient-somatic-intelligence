"""v0.4 stabilization container — Truth, Entropy, Isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.entropy import EntropyController
from kernel.isolation import ExecutionAudit, ExecutionScope, ResourceGuard, StateGuard
from kernel.truth import TruthGraph, TruthRegistry


@dataclass
class V04Stabilization:
    """Container for v0.4 Truth / Entropy / Isolation subsystems."""

    truth_graph: TruthGraph = field(default_factory=TruthGraph)
    truth_registry: TruthRegistry = field(default_factory=TruthRegistry)
    entropy_controller: EntropyController = field(default_factory=EntropyController)
    execution_scope: ExecutionScope = field(default_factory=ExecutionScope)
    resource_guard: ResourceGuard = field(default_factory=ResourceGuard)
    state_guard: StateGuard = field(default_factory=StateGuard)
    execution_audit: ExecutionAudit = field(default_factory=ExecutionAudit)
    _v04_connections: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.truth_registry.graph = self.truth_graph
        self.entropy_controller.drift_detector._graph = self.truth_graph
        self.state_guard.scope = self.execution_scope

    def snapshot(self) -> dict[str, Any]:
        entropy = self.entropy_controller.compute(
            self.truth_graph,
            bus_connections=self._v04_connections,
        )
        return {
            "truth": self.truth_graph.stats(),
            "entropy": entropy.to_dict(),
            "isolation": {
                "scope": self.execution_scope.stats(),
                "audit": self.execution_audit.stats(),
                "resource_denials": len(self.resource_guard.denials),
                "write_denials": len(self.state_guard.denials),
            },
            "connections": list(self._v04_connections),
        }


def boot_stabilization() -> V04Stabilization:
    """Instantiate all v0.4 stabilization subsystems."""
    return V04Stabilization()
