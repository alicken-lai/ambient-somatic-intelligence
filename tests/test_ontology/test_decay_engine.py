"""Tests for the Decay Engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.decay_engine import DecayEngine, DecayReport
from memory.ontology.decay_rules import DECAY_RULES, DECAY_RULE_REGISTRY
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.strategic_schema import StrategicEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_engine() -> DecayEngine:
    return DecayEngine(DECAY_RULES, ConfidenceModel())


def _make_episodic(
    entry_id: str = "ep001",
    confidence: float = 0.9,
    days_old: float = 10,
    last_accessed_days_ago: float | None = None,
) -> EpisodicEntry:
    ts = _utcnow() - timedelta(days=days_old)
    la = (
        _utcnow() - timedelta(days=last_accessed_days_ago)
        if last_accessed_days_ago is not None
        else None
    )
    return EpisodicEntry(
        entry_id=entry_id,
        timestamp=ts,
        source="test",
        content="test",
        tags=[],
        signal_types=[],
        environmental_context={},
        confidence=confidence,
        last_accessed=la,
    )


def _make_instinct(
    entry_id: str = "inst001",
    confidence: float = 0.8,
    days_old: float = 10,
    last_validated_days_ago: float | None = None,
) -> InstinctEntry:
    ts = _utcnow() - timedelta(days=days_old)
    lv = (
        _utcnow() - timedelta(days=last_validated_days_ago)
        if last_validated_days_ago is not None
        else None
    )
    return InstinctEntry(
        entry_id=entry_id,
        timestamp=ts,
        source_episodes=["ep001"],
        observation="test",
        trigger_conditions=[],
        confidence=confidence,
        last_validated=lv,
    )


def _make_strategic(
    entry_id: str = "strat001",
    confidence: float = 0.95,
    days_old: float = 10,
) -> StrategicEntry:
    ts = _utcnow() - timedelta(days=days_old)
    return StrategicEntry(
        entry_id=entry_id,
        timestamp=ts,
        source_skills=["skill001"],
        heuristic="test heuristic",
        applicability_scope="global",
        confidence=confidence,
        governance_approval_id="gov-001",
        verifier_id="ver-001",
    )


class TestTimeDecay:
    def test_reduces_confidence(self) -> None:
        engine = _make_engine()
        entry = _make_episodic(confidence=0.9, days_old=10)
        reports = engine.apply_time_decay([entry], _utcnow())
        assert len(reports) == 1
        assert reports[0].new_confidence < 0.9
        assert entry.confidence < 0.9

    def test_confidence_stays_above_floor(self) -> None:
        engine = _make_engine()
        entry = _make_episodic(confidence=0.02, days_old=100)
        reports = engine.apply_time_decay([entry], _utcnow())
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L1_EPISODIC]
        assert entry.confidence >= rule.min_confidence


class TestInactivityDecay:
    def test_accelerates_decay_for_inactive(self) -> None:
        engine = _make_engine()
        entry = _make_episodic(confidence=0.9, days_old=20, last_accessed_days_ago=15)
        reports = engine.apply_inactivity_decay([entry], _utcnow())
        assert len(reports) == 1
        assert reports[0].decay_reason == "inactivity"
        assert entry.confidence < 0.9

    def test_no_decay_if_recently_accessed(self) -> None:
        engine = _make_engine()
        entry = _make_episodic(confidence=0.9, days_old=20, last_accessed_days_ago=1)
        reports = engine.apply_inactivity_decay([entry], _utcnow())
        assert len(reports) == 0


class TestContradiction:
    def test_reduces_confidence_immediately(self) -> None:
        engine = _make_engine()
        entry = _make_instinct(confidence=0.8)
        report = engine.apply_contradiction(entry, "contradicting evidence found")
        assert report.new_confidence < 0.8
        assert report.decay_reason == "contradiction"


class TestLayerDecayRates:
    def test_l4_decays_slower_than_l2(self) -> None:
        engine = _make_engine()

        instinct = _make_instinct(confidence=0.8, days_old=30)
        strategic = _make_strategic(confidence=0.8, days_old=30)

        reports_l2 = engine.apply_time_decay([instinct], _utcnow())
        reports_l4 = engine.apply_time_decay([strategic], _utcnow())

        l2_drop = 0.8 - reports_l2[0].new_confidence
        l4_drop = 0.8 - reports_l4[0].new_confidence
        assert l4_drop < l2_drop


class TestThresholdRemoval:
    def test_entries_below_threshold_flagged(self) -> None:
        engine = _make_engine()
        rule = DECAY_RULE_REGISTRY[MemoryLayer.L1_EPISODIC]
        entry = _make_episodic(confidence=rule.min_confidence, days_old=100)
        reports = engine.apply_time_decay([entry], _utcnow())
        assert len(reports) == 1
        assert reports[0].below_threshold is True
        assert reports[0].recommended_action == "remove"


class TestSweep:
    def test_covers_all_decay_types(self) -> None:
        engine = _make_engine()
        entries = [
            _make_episodic("ep1", confidence=0.9, days_old=5),
            _make_episodic("ep2", confidence=0.9, days_old=5, last_accessed_days_ago=10),
        ]
        reports = engine.sweep(entries, _utcnow())
        assert len(reports) == 2
        reasons = {r.decay_reason for r in reports}
        assert "time_decay" in reasons or "inactivity" in reasons


class TestFailedReuse:
    def test_reduces_confidence(self) -> None:
        engine = _make_engine()
        entry = _make_episodic(confidence=0.9)
        report = engine.apply_failed_reuse(entry, "produced wrong output")
        assert report.new_confidence < 0.9
        assert report.decay_reason == "failed_reuse"


class TestGenerateReport:
    def test_produces_readable_output(self) -> None:
        engine = _make_engine()
        entries = [
            _make_episodic("ep1", confidence=0.9, days_old=10),
            _make_episodic("ep2", confidence=0.02, days_old=100),
        ]
        reports = engine.sweep(entries, _utcnow())
        text = engine.generate_report(reports)
        assert "Decay Report" in text
        assert "ep1" in text or "ep2" in text

    def test_empty_report(self) -> None:
        engine = _make_engine()
        text = engine.generate_report([])
        assert "no entries affected" in text
