"""Typed event contracts for IntegrationBus v0.4 stabilization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContractField:
    name: str
    type_hint: str
    required: bool
    description: str = ""


@dataclass(frozen=True)
class EventContract:
    """Explicit contract for a cross-subsystem bus event."""

    name: str
    source: str
    target: str
    payload_type: str
    version: str = "v0.4-stabilization"
    mechanism: str = "callback"
    fields: tuple[ContractField, ...] = field(default_factory=tuple)
    description: str = ""

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for f in self.fields:
            if f.required and f.name not in payload:
                errors.append(f"missing required field: {f.name}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "target": self.target,
            "payload_type": self.payload_type,
            "version": self.version,
            "mechanism": self.mechanism,
            "description": self.description,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type_hint,
                    "required": f.required,
                    "description": f.description,
                }
                for f in self.fields
            ],
        }


V04_STABILIZATION_EVENT_CONTRACTS: tuple[EventContract, ...] = (
    EventContract(
        name="truth_node_registered",
        source="kernel.truth.registry",
        target="kernel.integration_bus",
        payload_type="TruthNodeRegistered",
        description="A subsystem registered an auditable truth node.",
        fields=(
            ContractField("node_id", "str", True),
            ContractField("domain", "str", True),
            ContractField("owner", "str", True),
            ContractField("checksum", "str", True),
        ),
    ),
    EventContract(
        name="entropy_score_computed",
        source="kernel.entropy.controller",
        target="kernel.integration_bus",
        payload_type="EntropyScoreComputed",
        description="Entropy controller computed a new system score.",
        fields=(
            ContractField("score", "float", True),
            ContractField("classification", "str", True),
            ContractField("metric_count", "int", True),
        ),
    ),
    EventContract(
        name="execution_context_entered",
        source="kernel.isolation.scope",
        target="kernel.isolation.audit",
        payload_type="ExecutionContextEntered",
        fields=(
            ContractField("context_id", "str", True),
            ContractField("caller", "str", True),
            ContractField("scope", "str", True),
        ),
    ),
    EventContract(
        name="execution_write_denied",
        source="kernel.isolation.state_guard",
        target="kernel.entropy.mutation_tracker",
        payload_type="ExecutionWriteDenied",
        fields=(
            ContractField("target", "str", True),
            ContractField("caller", "str", True),
            ContractField("reason", "str", True),
        ),
    ),
)

EVENT_CONTRACT_MAP: dict[str, EventContract] = {
    c.name: c for c in V04_STABILIZATION_EVENT_CONTRACTS
}
