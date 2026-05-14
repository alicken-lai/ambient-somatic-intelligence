"""Tests for the Promotion Engine."""

from __future__ import annotations

from datetime import datetime, timezone

from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.promotion_engine import (
    PromotionCandidate,
    PromotionEngine,
    PromotionResult,
)
from memory.ontology.promotion_rules import PROMOTION_RULES
from memory.ontology.skill_schema import SkillMemoryEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_engine() -> PromotionEngine:
    return PromotionEngine(PROMOTION_RULES, ConfidenceModel())


def _make_episodic(entry_id: str = "ep001", confidence: float = 0.8, access_count: int = 5) -> EpisodicEntry:
    return EpisodicEntry(
        entry_id=entry_id,
        timestamp=_utcnow(),
        source="test",
        content="test signal",
        tags=["test"],
        signal_types=["test"],
        environmental_context={},
        confidence=confidence,
        access_count=access_count,
    )


def _make_instinct(entry_id: str = "inst001", confidence: float = 0.85, occurrence_count: int = 6) -> InstinctEntry:
    return InstinctEntry(
        entry_id=entry_id,
        timestamp=_utcnow(),
        source_episodes=["ep001"],
        observation="test observation",
        trigger_conditions=["trigger"],
        confidence=confidence,
        contextual_applicability=["ctx1", "ctx2"],
        occurrence_count=occurrence_count,
        success_count=5,
        failure_count=1,
    )


def _make_skill(entry_id: str = "skill001", confidence: float = 0.92) -> SkillMemoryEntry:
    return SkillMemoryEntry(
        entry_id=entry_id,
        timestamp=_utcnow(),
        source_instincts=["inst001"],
        skill_name="test_skill",
        description="A test skill",
        workflow_steps=["step1", "step2"],
        confidence=confidence,
        execution_count=12,
        success_count=11,
        failure_count=1,
        contexts_validated=["ctx1", "ctx2", "ctx3"],
    )


class TestScanCandidates:
    def test_finds_eligible_entries(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic(confidence=0.8, access_count=5)]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        assert len(candidates) == 1
        assert candidates[0].eligible is True

    def test_marks_ineligible_when_low_confidence(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic(confidence=0.3, access_count=5)]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        assert len(candidates) == 1
        assert candidates[0].eligible is False
        assert any("Confidence" in r for r in candidates[0].blocking_reasons)

    def test_marks_ineligible_when_low_occurrences(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic(confidence=0.8, access_count=1)]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        assert candidates[0].eligible is False
        assert any("Occurrences" in r for r in candidates[0].blocking_reasons)

    def test_skips_wrong_layer(self) -> None:
        engine = _make_engine()
        entries = [_make_instinct()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        assert len(candidates) == 0


class TestProposePromotion:
    def test_creates_proper_candidate(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        proposed = engine.propose_promotion(candidates[0])
        assert proposed.candidate_id
        assert len(engine.get_pending()) == 1

    def test_audit_log_records_proposal(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        engine.propose_promotion(candidates[0])
        log = engine.audit_log()
        assert len(log) == 1
        assert log[0]["action"] == "proposed"


class TestApprovePromotion:
    def test_requires_governance_decision_id(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        proposed = engine.propose_promotion(candidates[0])
        result = engine.approve_promotion(proposed.candidate_id, governance_decision_id="")
        assert result.approved is False
        assert "Governance" in result.reason

    def test_successful_approval(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        proposed = engine.propose_promotion(candidates[0])
        result = engine.approve_promotion(proposed.candidate_id, governance_decision_id="gov-001")
        assert result.approved is True
        assert result.new_entry_id is not None

    def test_l3_to_l4_requires_verifier(self) -> None:
        engine = _make_engine()
        entries = [_make_skill(confidence=0.92)]
        candidates = engine.scan_candidates(entries, MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) == 1
        proposed = engine.propose_promotion(eligible[0])
        result = engine.approve_promotion(
            proposed.candidate_id,
            governance_decision_id="gov-001",
            verifier_id=None,
        )
        assert result.approved is False
        assert "verifier_id" in result.reason

    def test_l3_to_l4_with_verifier_succeeds(self) -> None:
        engine = _make_engine()
        entries = [_make_skill(confidence=0.92)]
        candidates = engine.scan_candidates(entries, MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        proposed = engine.propose_promotion(eligible[0])
        result = engine.approve_promotion(
            proposed.candidate_id,
            governance_decision_id="gov-001",
            verifier_id="ver-001",
        )
        assert result.approved is True


class TestRejectPromotion:
    def test_reject(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        proposed = engine.propose_promotion(candidates[0])
        result = engine.reject_promotion(proposed.candidate_id, "Not ready")
        assert result.approved is False
        assert result.reason == "Not ready"


class TestRollbackPromotion:
    def test_rollback_reverses_approval(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        proposed = engine.propose_promotion(candidates[0])
        result = engine.approve_promotion(proposed.candidate_id, governance_decision_id="gov-001")
        assert result.approved is True

        rolled_back = engine.rollback_promotion(result)
        assert rolled_back is True
        assert result.approved is False

    def test_rollback_of_rejected_fails(self) -> None:
        engine = _make_engine()
        entries = [_make_episodic()]
        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        proposed = engine.propose_promotion(candidates[0])
        result = engine.reject_promotion(proposed.candidate_id, "nope")
        rolled_back = engine.rollback_promotion(result)
        assert rolled_back is False


class TestAuditLog:
    def test_captures_all_decisions(self) -> None:
        engine = _make_engine()

        ep1 = _make_episodic("ep1")
        ep2 = _make_episodic("ep2")
        entries = [ep1, ep2]

        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        p1 = engine.propose_promotion(candidates[0])
        p2 = engine.propose_promotion(candidates[1])

        engine.approve_promotion(p1.candidate_id, governance_decision_id="gov-001")
        engine.reject_promotion(p2.candidate_id, "not needed")

        log = engine.audit_log()
        actions = [entry["action"] for entry in log]
        assert "proposed" in actions
        assert "approved" in actions
        assert "rejected" in actions
