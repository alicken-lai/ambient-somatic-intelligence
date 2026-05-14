"""Tests for the Guardian verification doctrine (Phase 4)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from governance.doctrine.confidence_validation import (
    ConfidenceValidator,
    VerificationPolicy,
    VerificationRequest,
    VerificationResult,
)


@pytest.fixture
def validator() -> ConfidenceValidator:
    return ConfidenceValidator()


@pytest.fixture
def strict_validator() -> ConfidenceValidator:
    return ConfidenceValidator(
        policy=VerificationPolicy(min_verifier_confidence=0.8)
    )


# ── request_verification ──────────────────────────────────────────────────


class TestRequestVerification:

    def test_creates_proper_request(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification(
            artifact_id="art-01",
            artifact_type="skill_candidate",
            implementer_id="agent-A",
        )
        assert isinstance(req, VerificationRequest)
        assert req.artifact_id == "art-01"
        assert req.implementer_id == "agent-A"
        assert req.request_id  # non-empty

    def test_request_appears_in_pending(self, validator: ConfidenceValidator) -> None:
        validator.request_verification("art-01", "skill_candidate", "agent-A")
        pending = validator.get_pending_verifications()
        assert len(pending) == 1
        assert pending[0].artifact_id == "art-01"


# ── submit_verification — self-certification ──────────────────────────────


class TestSelfCertificationRejected:

    def test_rejects_same_agent(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-01", "skill_candidate", "agent-A")
        with pytest.raises(ValueError, match="Self-certification"):
            validator.submit_verification(
                request_id=req.request_id,
                verifier_id="agent-A",
                confidence=0.9,
                approved=True,
            )

    def test_accepts_different_agent(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-01", "skill_candidate", "agent-A")
        result = validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.9,
            approved=True,
        )
        assert isinstance(result, VerificationResult)
        assert result.approved is True


# ── check_promotion_allowed ───────────────────────────────────────────────


class TestCheckPromotionAllowed:

    def test_blocks_l2_without_verification(self, validator: ConfidenceValidator) -> None:
        allowed, reasons = validator.check_promotion_allowed("art-01", target_layer=2)
        assert allowed is False
        assert any("No verification" in r for r in reasons)

    def test_allows_l1_self_certification(self, validator: ConfidenceValidator) -> None:
        allowed, reasons = validator.check_promotion_allowed("art-01", target_layer=1)
        assert allowed is True
        assert reasons == []

    def test_allows_l2_with_good_verification(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-02", "promotion_proposal", "agent-A")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.85,
            approved=True,
        )
        allowed, reasons = validator.check_promotion_allowed("art-02", target_layer=2)
        assert allowed is True

    def test_blocks_l3_without_verification(self, validator: ConfidenceValidator) -> None:
        allowed, reasons = validator.check_promotion_allowed("art-03", target_layer=3)
        assert allowed is False

    def test_blocks_l4_without_verification(self, validator: ConfidenceValidator) -> None:
        allowed, reasons = validator.check_promotion_allowed("art-04", target_layer=4)
        assert allowed is False


# ── Low confidence flagging ───────────────────────────────────────────────


class TestLowConfidenceFlagged:

    def test_low_confidence_blocks_promotion(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-05", "skill_candidate", "agent-A")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.3,
            approved=True,
        )
        allowed, reasons = validator.check_promotion_allowed("art-05", target_layer=2)
        assert allowed is False
        assert any("below" in r.lower() for r in reasons)

    def test_escalation_recommended_on_low_confidence(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-06", "skill_candidate", "agent-A")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.4,
            approved=True,
        )
        _, reasons = validator.check_promotion_allowed("art-06", target_layer=2)
        assert any("escalation" in r.lower() for r in reasons)


# ── needs_reverification ──────────────────────────────────────────────────


class TestNeedsReverification:

    def test_needs_reverification_when_no_history(self, validator: ConfidenceValidator) -> None:
        assert validator.needs_reverification("art-new") is True

    def test_needs_reverification_after_expiry(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-07", "skill_candidate", "agent-A")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.9,
            approved=True,
        )
        future = datetime.now(timezone.utc) + timedelta(days=31)
        assert validator.needs_reverification("art-07", current_time=future) is True

    def test_no_reverification_within_window(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-08", "skill_candidate", "agent-A")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.9,
            approved=True,
        )
        soon = datetime.now(timezone.utc) + timedelta(days=5)
        assert validator.needs_reverification("art-08", current_time=soon) is False


# ── audit_trail ───────────────────────────────────────────────────────────


class TestAuditTrail:

    def test_captures_all_decisions(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-09", "skill_candidate", "agent-A")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.85,
            approved=True,
        )
        trail = validator.audit_trail()
        assert len(trail) >= 2  # request + result
        types = {entry["type"] for entry in trail}
        assert "verification_completed" in types

    def test_trail_includes_artifact_id(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-10", "promotion_proposal", "agent-X")
        validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-Y",
            confidence=0.75,
            approved=True,
        )
        trail = validator.audit_trail()
        artifact_ids = {e.get("artifact_id") for e in trail}
        assert "art-10" in artifact_ids


# ── blocking_issues ───────────────────────────────────────────────────────


class TestBlockingIssues:

    def test_blocking_issues_prevent_approval(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-11", "strategic_rule", "agent-A")
        result = validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.9,
            approved=True,
            blocking_issues=["Evidence is circular"],
        )
        assert result.approved is False
        assert "Evidence is circular" in result.blocking_issues

    def test_no_blocking_issues_allows_approval(self, validator: ConfidenceValidator) -> None:
        req = validator.request_verification("art-12", "skill_candidate", "agent-A")
        result = validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-B",
            confidence=0.9,
            approved=True,
            blocking_issues=[],
        )
        assert result.approved is True
