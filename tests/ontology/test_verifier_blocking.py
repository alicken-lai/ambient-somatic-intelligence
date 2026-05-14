"""Phase 0F — Verifier Independence Stress Test.

Verifies that self-certification is blocked, independent verification is required
for L2+ promotions, and all governance actions are audited.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.promotion_engine import PromotionEngine
from memory.ontology.promotion_rules import PROMOTION_RULES
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.skill_schema import SkillMemoryEntry
from governance.doctrine.confidence_validation import (
    ConfidenceValidator,
    VerificationPolicy,
    VerificationRequest,
    VerificationResult,
)


IMPLEMENTER_ID = "agent-llm-001"
INDEPENDENT_VERIFIER = "agent-verifier-002"


@pytest.fixture
def validator():
    return ConfidenceValidator()


@pytest.fixture
def strict_policy_validator():
    policy = VerificationPolicy(
        min_verifier_confidence=0.7,
        require_different_agent=True,
        max_self_certification_layer=1,
        escalate_on_low_confidence=True,
        max_verification_age_days=30,
    )
    return ConfidenceValidator(policy=policy)


class TestSelfCertificationBlocked:
    def test_self_certification_blocked(self, validator):
        """Self-verification (implementer == verifier) must raise ValueError."""
        req = validator.request_verification(
            artifact_id="skill-001",
            artifact_type="skill_candidate",
            implementer_id=IMPLEMENTER_ID,
        )
        with pytest.raises(ValueError, match="Self-certification rejected"):
            validator.submit_verification(
                request_id=req.request_id,
                verifier_id=IMPLEMENTER_ID,
                confidence=0.9,
                approved=True,
            )


class TestIndependentVerifierAccepted:
    def test_independent_verifier_accepted(self, validator):
        """Independent verifier (different ID) should succeed."""
        req = validator.request_verification(
            artifact_id="skill-002",
            artifact_type="skill_candidate",
            implementer_id=IMPLEMENTER_ID,
        )
        result = validator.submit_verification(
            request_id=req.request_id,
            verifier_id=INDEPENDENT_VERIFIER,
            confidence=0.85,
            approved=True,
        )
        assert result.approved
        assert result.verifier_id == INDEPENDENT_VERIFIER


class TestL1AllowsSelfCertification:
    def test_l1_allows_self_certification(self, validator):
        """L1 promotion does not require independent verification (max_self_certification_layer=1)."""
        allowed, reasons = validator.check_promotion_allowed(
            artifact_id="some-l1-artifact",
            target_layer=1,
        )
        assert allowed
        assert len(reasons) == 0


class TestL2BlocksSelfCertification:
    def test_l2_blocks_self_certification(self, validator):
        """L2 promotion without any verification should be blocked."""
        allowed, reasons = validator.check_promotion_allowed(
            artifact_id="unverified-artifact",
            target_layer=2,
        )
        assert not allowed
        assert any("verification" in r.lower() for r in reasons)


class TestL3ToL4RequiresVerifierId:
    def test_l3_to_l4_requires_verifier_id(self, promotion_engine):
        """Promotion engine rejects L3→L4 without verifier_id."""
        skill = SkillMemoryEntry(
            entry_id="skill-l4-test",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-001"],
            skill_name="test_skill",
            description="test",
            workflow_steps=["step1"],
            confidence=0.95,
            execution_count=15,
            success_count=14,
            failure_count=1,
            contexts_validated=["ctx_a", "ctx_b"],
        )
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])
        result = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="gov-test",
            verifier_id=None,
        )
        assert not result.approved
        assert "verifier" in result.reason.lower()


class TestLowConfidenceVerificationFlagged:
    def test_low_confidence_verification_flagged(self, strict_policy_validator):
        """Verification with confidence below policy threshold should block promotion."""
        req = strict_policy_validator.request_verification(
            artifact_id="skill-low-conf",
            artifact_type="skill_candidate",
            implementer_id=IMPLEMENTER_ID,
        )
        strict_policy_validator.submit_verification(
            request_id=req.request_id,
            verifier_id=INDEPENDENT_VERIFIER,
            confidence=0.5,
            approved=True,
        )
        allowed, reasons = strict_policy_validator.check_promotion_allowed(
            artifact_id="skill-low-conf",
            target_layer=3,
        )
        assert not allowed
        assert any("confidence" in r.lower() for r in reasons)


class TestExpiredVerificationNeedsRenewal:
    def test_expired_verification_needs_renewal(self, validator):
        """Verification older than max_verification_age_days needs re-verification."""
        req = validator.request_verification(
            artifact_id="skill-expired",
            artifact_type="skill_candidate",
            implementer_id=IMPLEMENTER_ID,
        )
        result = validator.submit_verification(
            request_id=req.request_id,
            verifier_id=INDEPENDENT_VERIFIER,
            confidence=0.9,
            approved=True,
        )
        future = datetime.now(timezone.utc) + timedelta(days=60)
        needs_renewal = validator.needs_reverification("skill-expired", current_time=future)
        assert needs_renewal


class TestAllVerificationActionsAudited:
    def test_all_verification_actions_audited(self, validator):
        """All verification requests and results must appear in audit trail."""
        req = validator.request_verification(
            artifact_id="skill-audit",
            artifact_type="skill_candidate",
            implementer_id=IMPLEMENTER_ID,
        )
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id=INDEPENDENT_VERIFIER,
            confidence=0.9,
            approved=True,
        )
        trail = validator.audit_trail()
        assert len(trail) >= 2
        types = [entry["type"] for entry in trail]
        assert "request_completed" in types
        assert "verification_completed" in types


class TestGovernanceBlockEntriesLogged:
    def test_governance_block_entries_logged(self, promotion_engine):
        """Blocked promotions must appear in the promotion engine's audit log."""
        skill = SkillMemoryEntry(
            entry_id="skill-block-log",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-001"],
            skill_name="blocked_skill",
            description="test",
            workflow_steps=["step1"],
            confidence=0.95,
            execution_count=15,
            success_count=14,
            failure_count=1,
            contexts_validated=["ctx_a", "ctx_b"],
        )
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])
        promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="gov-test",
            verifier_id=None,
        )
        audit = promotion_engine.audit_log()
        actions = [a["action"] for a in audit]
        assert "rejected_no_verifier" in actions
