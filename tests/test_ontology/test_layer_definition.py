"""Tests for the 4-layer memory ontology definition."""

from __future__ import annotations

from memory.ontology.layer_definition import (
    LAYER_REGISTRY,
    LayerDefinition,
    MemoryLayer,
)


class TestMemoryLayerEnum:
    def test_all_four_layers_defined(self) -> None:
        assert len(MemoryLayer) == 4

    def test_layer_ordering(self) -> None:
        assert MemoryLayer.L1_EPISODIC < MemoryLayer.L2_INSTINCT
        assert MemoryLayer.L2_INSTINCT < MemoryLayer.L3_SKILL
        assert MemoryLayer.L3_SKILL < MemoryLayer.L4_STRATEGIC

    def test_layer_values(self) -> None:
        assert MemoryLayer.L1_EPISODIC == 1
        assert MemoryLayer.L2_INSTINCT == 2
        assert MemoryLayer.L3_SKILL == 3
        assert MemoryLayer.L4_STRATEGIC == 4


class TestLayerRegistry:
    def test_registry_completeness(self) -> None:
        for layer in MemoryLayer:
            assert layer in LAYER_REGISTRY

    def test_registry_length(self) -> None:
        assert len(LAYER_REGISTRY) == 4

    def test_l1_defaults(self) -> None:
        defn = LAYER_REGISTRY[MemoryLayer.L1_EPISODIC]
        assert defn.retention_policy == "30d"
        assert defn.promotion_threshold == 0.7
        assert defn.decay_rate == 0.1
        assert defn.max_entries == 10000
        assert defn.governance_required_for_promotion is False

    def test_l2_defaults(self) -> None:
        defn = LAYER_REGISTRY[MemoryLayer.L2_INSTINCT]
        assert defn.retention_policy == "180d"
        assert defn.promotion_threshold == 0.8
        assert defn.decay_rate == 0.03
        assert defn.max_entries == 5000
        assert defn.governance_required_for_promotion is True

    def test_l3_defaults(self) -> None:
        defn = LAYER_REGISTRY[MemoryLayer.L3_SKILL]
        assert defn.retention_policy == "365d"
        assert defn.promotion_threshold == 0.9
        assert defn.decay_rate == 0.01
        assert defn.max_entries == 1000
        assert defn.governance_required_for_promotion is True

    def test_l4_defaults(self) -> None:
        defn = LAYER_REGISTRY[MemoryLayer.L4_STRATEGIC]
        assert defn.retention_policy == "unlimited"
        assert defn.decay_rate == 0.003
        assert defn.max_entries == 200
        assert defn.governance_required_for_promotion is True


class TestLayerDefinitionSerialization:
    def test_to_dict_roundtrip(self) -> None:
        defn = LAYER_REGISTRY[MemoryLayer.L1_EPISODIC]
        data = defn.to_dict()
        restored = LayerDefinition.from_dict(data)
        assert restored.layer == defn.layer
        assert restored.name == defn.name
        assert restored.decay_rate == defn.decay_rate
