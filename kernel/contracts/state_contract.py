"""Typed state contracts for kernel stabilization snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class StateField:
    name: str
    type_hint: str
    description: str = ""


@dataclass(frozen=True)
class StateContract:
    """Contract for a named kernel state snapshot."""

    name: str
    owner_subsystem: str
    version: str
    fields: tuple[StateField, ...] = field(default_factory=tuple)
    description: str = ""

    def validate_snapshot(self, snapshot: dict[str, Any]) -> list[str]:
        return [
            f"missing state field: {f.name}"
            for f in self.fields
            if f.name not in snapshot
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "owner_subsystem": self.owner_subsystem,
            "version": self.version,
            "description": self.description,
            "fields": [
                {"name": f.name, "type": f.type_hint, "description": f.description}
                for f in self.fields
            ],
        }


V04_STATE_CONTRACTS: tuple[StateContract, ...] = (
    StateContract(
        name="truth_graph_state",
        owner_subsystem="kernel.truth",
        version="1.0.0",
        fields=(
            StateField("node_count", "int"),
            StateField("edge_count", "int"),
            StateField("conflicts", "int"),
            StateField("stale_count", "int"),
        ),
        description="Truth graph integrity snapshot.",
    ),
    StateContract(
        name="entropy_state",
        owner_subsystem="kernel.entropy",
        version="1.0.0",
        fields=(
            StateField("score", "float"),
            StateField("classification", "str"),
            StateField("breakdown", "dict"),
        ),
        description="Latest entropy assessment.",
    ),
    StateContract(
        name="isolation_state",
        owner_subsystem="kernel.isolation",
        version="1.0.0",
        fields=(
            StateField("active_contexts", "int"),
            StateField("violation_count", "int"),
            StateField("audit_total", "int"),
        ),
        description="Execution isolation snapshot.",
    ),
)

STATE_CONTRACT_MAP: dict[str, StateContract] = {
    c.name: c for c in V04_STATE_CONTRACTS
}


def capture_state(
    contract: StateContract,
    provider: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Capture and validate a state snapshot against a contract."""
    snapshot = provider()
    errors = contract.validate_snapshot(snapshot)
    if errors:
        snapshot["_validation_errors"] = errors
    snapshot["_contract"] = contract.name
    return snapshot
