"""Formal 4-layer memory ontology for Ambient OS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class MemoryLayer(IntEnum):
    L1_EPISODIC = 1
    L2_INSTINCT = 2
    L3_SKILL = 3
    L4_STRATEGIC = 4


@dataclass
class LayerDefinition:
    layer: MemoryLayer
    name: str
    description: str
    retention_policy: str
    promotion_threshold: float
    decay_rate: float
    max_entries: int
    governance_required_for_promotion: bool

    def to_dict(self) -> dict:
        return {
            "layer": self.layer.value,
            "name": self.name,
            "description": self.description,
            "retention_policy": self.retention_policy,
            "promotion_threshold": self.promotion_threshold,
            "decay_rate": self.decay_rate,
            "max_entries": self.max_entries,
            "governance_required_for_promotion": self.governance_required_for_promotion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LayerDefinition:
        return cls(
            layer=MemoryLayer(data["layer"]),
            name=data["name"],
            description=data["description"],
            retention_policy=data["retention_policy"],
            promotion_threshold=data["promotion_threshold"],
            decay_rate=data["decay_rate"],
            max_entries=data["max_entries"],
            governance_required_for_promotion=data["governance_required_for_promotion"],
        )


LAYER_REGISTRY: dict[MemoryLayer, LayerDefinition] = {
    MemoryLayer.L1_EPISODIC: LayerDefinition(
        layer=MemoryLayer.L1_EPISODIC,
        name="Episodic",
        description="Raw episodic memory — unprocessed observations and events",
        retention_policy="30d",
        promotion_threshold=0.7,
        decay_rate=0.1,
        max_entries=10000,
        governance_required_for_promotion=False,
    ),
    MemoryLayer.L2_INSTINCT: LayerDefinition(
        layer=MemoryLayer.L2_INSTINCT,
        name="Instinct",
        description="Atomic reusable observations distilled from episodic patterns",
        retention_policy="180d",
        promotion_threshold=0.8,
        decay_rate=0.03,
        max_entries=5000,
        governance_required_for_promotion=True,
    ),
    MemoryLayer.L3_SKILL: LayerDefinition(
        layer=MemoryLayer.L3_SKILL,
        name="Skill",
        description="Clustered workflows and procedures validated across contexts",
        retention_policy="365d",
        promotion_threshold=0.9,
        decay_rate=0.01,
        max_entries=1000,
        governance_required_for_promotion=True,
    ),
    MemoryLayer.L4_STRATEGIC: LayerDefinition(
        layer=MemoryLayer.L4_STRATEGIC,
        name="Strategic",
        description="Decision heuristics and metacognitive rules — highest-trust memory",
        retention_policy="unlimited",
        promotion_threshold=-1.0,
        decay_rate=0.003,
        max_entries=200,
        governance_required_for_promotion=True,
    ),
}
