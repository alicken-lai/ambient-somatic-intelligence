"""Routing contracts — typed bus route definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RouteMechanism(str, Enum):
    CALLBACK = "callback"
    ADAPTER = "adapter"
    OBSERVER = "observer"


@dataclass(frozen=True)
class BusRoute:
    """A typed route on the integration bus."""

    name: str
    source: str
    target: str
    event_contract: str
    mechanism: RouteMechanism = RouteMechanism.CALLBACK
    reversible: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "target": self.target,
            "event_contract": self.event_contract,
            "mechanism": self.mechanism.value,
            "reversible": self.reversible,
            "description": self.description,
        }


V04_STABILIZATION_ROUTES: tuple[BusRoute, ...] = (
    BusRoute(
        name="bus_to_truth_registry",
        source="kernel.integration_bus",
        target="kernel.truth.registry",
        event_contract="truth_node_registered",
        mechanism=RouteMechanism.OBSERVER,
        description="Bus events register canonical truth nodes on lifecycle hooks.",
    ),
    BusRoute(
        name="truth_to_entropy",
        source="kernel.truth.graph",
        target="kernel.entropy.controller",
        event_contract="entropy_score_computed",
        mechanism=RouteMechanism.OBSERVER,
        description="Truth graph changes trigger entropy recompute (read-only).",
    ),
    BusRoute(
        name="isolation_to_entropy",
        source="kernel.isolation.state_guard",
        target="kernel.entropy.mutation_tracker",
        event_contract="execution_write_denied",
        mechanism=RouteMechanism.CALLBACK,
        description="Denied writes feed mutation pressure metrics.",
    ),
    BusRoute(
        name="entropy_to_somatic",
        source="kernel.entropy.controller",
        target="somatic.bus",
        event_contract="entropy_pressure_signal",
        mechanism=RouteMechanism.ADAPTER,
        reversible=False,
        description="Unstable entropy emits somatic pressure (observable only).",
    ),
    BusRoute(
        name="governance_to_isolation",
        source="governance.mandatory_gate",
        target="kernel.isolation.audit",
        event_contract="execution_context_entered",
        mechanism=RouteMechanism.ADAPTER,
        description="Gate checks logged to execution audit (adapter, no gate changes).",
    ),
)

ROUTE_MAP: dict[str, BusRoute] = {r.name: r for r in V04_STABILIZATION_ROUTES}
