"""Tests for all memory ontology schemas (L1–L4)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.skill_schema import SkillMemoryEntry
from memory.ontology.strategic_schema import StrategicEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestEpisodicEntry:
    def _make(self, **overrides) -> EpisodicEntry:
        defaults = dict(
            entry_id="ep001",
            timestamp=_utcnow(),
            source="test_module",
            content="cpu spike detected",
            tags=["cpu", "anomaly"],
            signal_types=["cpu_spike"],
            environmental_context={"cpu_band": "heavy"},
            confidence=1.0,
        )
        defaults.update(overrides)
        return EpisodicEntry(**defaults)

    def test_creation(self) -> None:
        e = self._make()
        assert e.entry_id == "ep001"
        assert e.layer == MemoryLayer.L1_EPISODIC

    def test_to_dict_roundtrip(self) -> None:
        e = self._make()
        data = e.to_dict()
        restored = EpisodicEntry.from_dict(data)
        assert restored.entry_id == e.entry_id
        assert restored.content == e.content
        assert restored.layer == MemoryLayer.L1_EPISODIC

    def test_age_days(self) -> None:
        ts = _utcnow() - timedelta(days=5)
        e = self._make(timestamp=ts)
        age = e.age_days()
        assert 4.9 < age < 5.1

    def test_is_promotion_candidate_true(self) -> None:
        e = self._make(confidence=0.8)
        assert e.is_promotion_candidate(0.7) is True

    def test_is_promotion_candidate_false(self) -> None:
        e = self._make(confidence=0.5)
        assert e.is_promotion_candidate(0.7) is False


class TestInstinctEntry:
    def _make(self, **overrides) -> InstinctEntry:
        defaults = dict(
            entry_id="inst001",
            timestamp=_utcnow(),
            source_episodes=["ep001", "ep002"],
            observation="validate input before processing",
            trigger_conditions=["new_input"],
            confidence=0.75,
            occurrence_count=5,
            success_count=4,
            failure_count=1,
        )
        defaults.update(overrides)
        return InstinctEntry(**defaults)

    def test_creation(self) -> None:
        i = self._make()
        assert i.layer == MemoryLayer.L2_INSTINCT

    def test_success_rate(self) -> None:
        i = self._make(success_count=4, failure_count=1)
        assert i.success_rate() == 0.8

    def test_success_rate_zero_total(self) -> None:
        i = self._make(success_count=0, failure_count=0)
        assert i.success_rate() == 0.0

    def test_to_dict_roundtrip(self) -> None:
        i = self._make()
        data = i.to_dict()
        restored = InstinctEntry.from_dict(data)
        assert restored.observation == i.observation

    def test_is_promotion_candidate(self) -> None:
        i = self._make(confidence=0.85)
        assert i.is_promotion_candidate(0.8) is True
        assert i.is_promotion_candidate(0.9) is False

    def test_apply_contradiction(self) -> None:
        i = self._make(contradiction_count=0)
        i.apply_contradiction()
        assert i.contradiction_count == 1
        i.apply_contradiction()
        assert i.contradiction_count == 2


class TestSkillMemoryEntry:
    def _make(self, **overrides) -> SkillMemoryEntry:
        defaults = dict(
            entry_id="skill001",
            timestamp=_utcnow(),
            source_instincts=["inst001", "inst002"],
            skill_name="anomaly_detection_pipeline",
            description="Detects CPU anomalies via sensor fusion",
            workflow_steps=["collect", "evaluate", "report"],
            confidence=0.85,
            execution_count=10,
            success_count=8,
            failure_count=2,
            contexts_validated=["production", "staging"],
        )
        defaults.update(overrides)
        return SkillMemoryEntry(**defaults)

    def test_success_rate(self) -> None:
        s = self._make()
        assert s.success_rate() == 0.8

    def test_cross_context_count(self) -> None:
        s = self._make()
        assert s.cross_context_count() == 2

    def test_to_dict_roundtrip(self) -> None:
        s = self._make()
        data = s.to_dict()
        restored = SkillMemoryEntry.from_dict(data)
        assert restored.skill_name == s.skill_name

    def test_is_promotion_candidate(self) -> None:
        s = self._make(confidence=0.95)
        assert s.is_promotion_candidate(0.9) is True


class TestStrategicEntry:
    def _make(self, **overrides) -> StrategicEntry:
        defaults = dict(
            entry_id="strat001",
            timestamp=_utcnow(),
            source_skills=["skill001"],
            heuristic="Always verify before trust",
            applicability_scope="global",
            confidence=0.95,
            governance_approval_id="gov-001",
            verifier_id="ver-001",
        )
        defaults.update(overrides)
        return StrategicEntry(**defaults)

    def test_is_valid_with_governance(self) -> None:
        s = self._make()
        assert s.is_valid() is True

    def test_is_valid_without_governance(self) -> None:
        s = self._make(governance_approval_id="")
        assert s.is_valid() is False

    def test_to_dict_roundtrip(self) -> None:
        s = self._make()
        data = s.to_dict()
        restored = StrategicEntry.from_dict(data)
        assert restored.heuristic == s.heuristic
        assert restored.layer == MemoryLayer.L4_STRATEGIC

    def test_apply_contradiction(self) -> None:
        s = self._make(contradiction_count=0)
        s.apply_contradiction()
        assert s.contradiction_count == 1
