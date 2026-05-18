"""Typed integration bus contracts — v0.4 stabilization."""

from kernel.contracts.event_contract import (
    EVENT_CONTRACT_MAP,
    V04_STABILIZATION_EVENT_CONTRACTS,
    ContractField,
    EventContract,
)
from kernel.contracts.routing_contract import (
    ROUTE_MAP,
    V04_STABILIZATION_ROUTES,
    BusRoute,
    RouteMechanism,
)
from kernel.contracts.signal_contract import (
    SIGNAL_CONTRACT_MAP,
    V04_SIGNAL_CONTRACTS,
    SignalContract,
)
from kernel.contracts.state_contract import (
    STATE_CONTRACT_MAP,
    V04_STATE_CONTRACTS,
    StateContract,
    StateField,
    capture_state,
)

__all__ = [
    "BusRoute",
    "ContractField",
    "EventContract",
    "RouteMechanism",
    "SignalContract",
    "StateContract",
    "StateField",
    "V04_SIGNAL_CONTRACTS",
    "V04_STABILIZATION_EVENT_CONTRACTS",
    "V04_STABILIZATION_ROUTES",
    "V04_STATE_CONTRACTS",
    "EVENT_CONTRACT_MAP",
    "ROUTE_MAP",
    "SIGNAL_CONTRACT_MAP",
    "STATE_CONTRACT_MAP",
    "capture_state",
]
