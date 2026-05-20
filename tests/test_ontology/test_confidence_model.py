"""Tests for the unified confidence lifecycle model."""

from __future__ import annotations

from datetime import datetime, timezone

from memory.ontology.confidence_model import ConfidenceModel, ConfidenceUpdate
from memory.ontology.decay_rules import DECAY_RULE_REGISTRY
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.layer_definition import MemoryLayer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_episodic(confidence: float = 0.5) -> EpisodicEntry:
    return EpisodicEntry(
        entry_id="ep001",
        timestamp=_utcnow(),
        source="test",
        content="test",
        tags=[],
        signal_types=[],
        environmental_context={},
        confidence=confidence,
    )


def _make_instinct(confidence: float = 0.5) -> InstinctEntry:
    return InstinctEntry(
        entry_id="inst001",
        timestamp=_utcnow(),
        source_episodes=["ep001"],
        observation="test",
        trigger_conditions=[],
        confidence=confidence,
    )


class TestUpdateOnSuccess:
    def test_increases_confidence(self) -> None:
        model = ConfidenceModel()
        entry = _make_episodic(confidence=0.5)
        update = model.update_on_success(entry)
        assert update.new_confidence > 0.5

    def test_never_exceeds_cap(self) -> None:
        model = ConfidenceModel()
        entry = _make_episodic(confidence=0.98)
        update = model.update_on_success(entry)
        assert update.new_confidence <= 0.99


class TestUpdateOnFailure:
    def test_decreases_confidence(self) -> None:
        model = ConfidenceModel()
        entry = _make_episodic(confidence=0.8)
        update = model.update_on_failure(entry)
        assert update.new_confidence < 0.8

    def test_respects_rule_floor(self) -> None:
        model = ConfidenceModel()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L1_EPISODIC]
        entry = _make_episodic(confidence=0.02)
        update = model.update_on_failure(entry, rule=rule)
        assert update.new_confidence >= rule.min_confidence


class TestUpdateOnContradiction:
    def test_applies_penalty(self) -> None:
        model = ConfidenceModel()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L2_INSTINCT]
        entry = _make_instinct(confidence=0.8)
        update = model.update_on_contradiction(entry, "evidence", rule=rule)
        assert update.new_confidence < 0.8

    def test_increments_contradiction_count(self) -> None:
        model = ConfidenceModel()
        entry = _make_instinct(confidence=0.8)
        model.update_on_contradiction(entry, "evidence")
        assert entry.contradiction_count == 1


class TestUpdateOnAccess:
    def test_small_increase(self) -> None:
        model = ConfidenceModel()
        entry = _make_episodic(confidence=0.5)
        update = model.update_on_access(entry)
        assert update.new_confidence > 0.5
        assert update.new_confidence - 0.5 < 0.02  # small bump


class TestApplyDecay:
    def test_reduces_over_time(self) -> None:
        model = ConfidenceModel()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L1_EPISODIC]
        entry = _make_episodic(confidence=0.9)
        update = model.apply_decay(entry, elapsed_days=10, rule=rule)
        assert update.new_confidence < 0.9


class TestConfidenceHistory:
    def test_append_only(self) -> None:
        model = ConfidenceModel()
        entry = _make_episodic(confidence=0.5)

        model.update_on_success(entry)
        model.update_on_success(entry)
        model.update_on_failure(entry)

        history = model.history.get_history("ep001")
        assert len(history) == 3
        assert all(isinstance(u, ConfidenceUpdate) for u in history)

    def test_global_history_grows(self) -> None:
        model = ConfidenceModel()
        e1 = _make_episodic(confidence=0.5)
        e2 = EpisodicEntry(
            entry_id="ep002",
            timestamp=_utcnow(),
            source="test",
            content="test2",
            tags=[],
            signal_types=[],
            environmental_context={},
            confidence=0.6,
        )

        model.update_on_success(e1)
        model.update_on_success(e2)

        assert len(model.history) == 2
        assert len(model.history.get_history("ep001")) == 1
        assert len(model.history.get_history("ep002")) == 1

    def test_confidence_never_below_zero(self) -> None:
        model = ConfidenceModel()
        entry = _make_episodic(confidence=0.05)
        for _ in range(20):
            model.update_on_failure(entry)
        assert entry.confidence >= 0.0
