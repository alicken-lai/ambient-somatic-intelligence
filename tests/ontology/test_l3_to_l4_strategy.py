"""L3→L4 Strategic Promotion Stress Test.

Verifies that skill-to-strategic promotion enforces high confidence (0.9),
min 10 occurrences, cross-project validation, and governance + verifier.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.skill_schema import SkillMemoryEntry
from memory.ontology.strategic_schema import StrategicEntry
from memory.ontology.promotion_rules import PROMOTION_RULES, check_promotion_eligibility
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.promotion_engine import PromotionEngine


L3_TO_L4_RULE = PROMOTION_RULES[2]


def _make_skill(
    confidence: float = 0.92,
    execution_count: int = 12,
    success_count: int = 11,
    failure_count: int = 1,
    contexts: list[str] | None = None,
) -> SkillMemoryEntry:
    return SkillMemoryEntry(
        entry_id=f"skill-strat-{uuid.uuid4().hex[:6]}",
        timestamp=datetime.now(timezone.utc),
        source_instincts=[f"inst-{uuid.uuid4().hex[:6]}" for _ in range(3)],
        skill_name="thermal_cross_domain_detection",
        description="Detect thermal issues across domains",
        workflow_steps=["collect", "analyze", "alert", "escalate"],
        confidence=confidence,
        execution_count=execution_count,
        success_count=success_count,
        failure_count=failure_count,
        contexts_validated=contexts or ["rack", "hvac", "vehicle"],
        last_executed=datetime.now(timezone.utc),
    )


class TestSkillToStrategicRequiresHighConfidence:
    def test_skill_to_strategic_requires_high_confidence(self, promotion_engine):
        """Confidence < 0.9 should block L3→L4 promotion."""
        low_conf_skill = _make_skill(confidence=0.85)
        candidates = promotion_engine.scan_candidates([low_conf_skill], MemoryLayer.L3_SKILL)
        for c in candidates:
            assert not c.eligible
            assert any("Confidence" in r for r in c.blocking_reasons)


class TestRequires10Occurrences:
    def test_requires_10_occurrences(self, promotion_engine):
        """execution_count < 10 should block L3→L4 promotion."""
        low_exec_skill = _make_skill(execution_count=8, success_count=7, failure_count=1)
        candidates = promotion_engine.scan_candidates([low_exec_skill], MemoryLayer.L3_SKILL)
        for c in candidates:
            assert not c.eligible
            assert any("Occurrences" in r for r in c.blocking_reasons)


class TestRequiresCrossProjectValidation:
    def test_requires_cross_project_validation(self, promotion_engine):
        """Single-context skill should not be eligible for L3→L4."""
        single_ctx = _make_skill(contexts=["only_one"])
        candidates = promotion_engine.scan_candidates([single_ctx], MemoryLayer.L3_SKILL)
        for c in candidates:
            assert not c.eligible
            assert any("Cross-context" in r for r in c.blocking_reasons)


class TestRequiresGovernanceAndVerifier:
    def test_requires_governance_and_verifier(self, promotion_engine):
        """L3→L4 requires both governance_decision_id and verifier_id."""
        skill = _make_skill()
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])

        result_no_gov = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="",
            verifier_id="verifier-001",
        )
        assert not result_no_gov.approved

    def test_requires_verifier_id(self, promotion_engine):
        """L3→L4 must fail without verifier_id even with governance."""
        skill = _make_skill()
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])

        result_no_verifier = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="gov-001",
            verifier_id=None,
        )
        assert not result_no_verifier.approved
        assert "verifier" in result_no_verifier.reason.lower()


class TestStrategicEntryHasGovernanceApprovalId:
    def test_strategic_entry_has_governance_approval_id(self, promotion_engine):
        """Successful L3→L4 promotion should return new_entry_id when all conditions met."""
        skill = _make_skill()
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])

        result = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="gov-approved-001",
            verifier_id="independent-verifier-001",
        )
        assert result.approved
        assert result.new_entry_id is not None
        assert result.governance_decision_id == "gov-approved-001"
        assert result.verifier_id == "independent-verifier-001"
