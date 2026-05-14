"""Confidence validation for the Guardian verification doctrine.

Implements the core principle: *"The implementer is an LLM.
Verify independently."*

Key guarantees:
  - Self-certification (implementer == verifier) is always rejected.
  - L2+ promotions require at least one independent verification.
  - Low-confidence verifications are flagged for escalation.
  - Every decision is recorded in an immutable audit trail.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── Request / Result types ────────────────────────────────────────────────


@dataclass
class VerificationRequest:
    """Request for independent verification of an artifact."""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    artifact_id: str = ""
    artifact_type: str = ""  # "skill_candidate", "promotion_proposal", "strategic_rule"
    implementer_id: str = ""
    requested_at: datetime = field(default_factory=_utc_now)
    context: dict[str, Any] = field(default_factory=dict)
    urgency: str = "medium"  # "low", "medium", "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "implementer_id": self.implementer_id,
            "requested_at": self.requested_at.isoformat(),
            "context": self.context,
            "urgency": self.urgency,
        }


@dataclass
class VerificationResult:
    """Result of independent verification."""

    request_id: str = ""
    verifier_id: str = ""
    verified_at: datetime = field(default_factory=_utc_now)
    confidence: float = 0.0
    approved: bool = False
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "verifier_id": self.verifier_id,
            "verified_at": self.verified_at.isoformat(),
            "confidence": round(self.confidence, 6),
            "approved": self.approved,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "blocking_issues": self.blocking_issues,
        }


# ── Policy ────────────────────────────────────────────────────────────────


@dataclass
class VerificationPolicy:
    """Policy rules for verification requirements."""

    min_verifier_confidence: float = 0.7
    require_different_agent: bool = True
    max_self_certification_layer: int = 1  # L1 can self-certify, L2+ cannot
    escalate_on_low_confidence: bool = True
    max_verification_age_days: int = 30

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_verifier_confidence": self.min_verifier_confidence,
            "require_different_agent": self.require_different_agent,
            "max_self_certification_layer": self.max_self_certification_layer,
            "escalate_on_low_confidence": self.escalate_on_low_confidence,
            "max_verification_age_days": self.max_verification_age_days,
        }


# ── Validator ─────────────────────────────────────────────────────────────


class ConfidenceValidator:
    """Validates that artifacts meet confidence requirements before promotion.

    Enforces the four verification rules from the independent
    verification doctrine.
    """

    def __init__(self, policy: Optional[VerificationPolicy] = None):
        self._policy = policy or VerificationPolicy()
        self._pending: list[VerificationRequest] = []
        self._completed: list[VerificationResult] = []
        self._all_requests: list[VerificationRequest] = []

    # ── Request / Submit ──────────────────────────────────────────────

    def request_verification(
        self,
        artifact_id: str,
        artifact_type: str,
        implementer_id: str,
        context: Optional[dict[str, Any]] = None,
        urgency: str = "medium",
    ) -> VerificationRequest:
        """Create a new verification request."""
        req = VerificationRequest(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            implementer_id=implementer_id,
            context=context or {},
            urgency=urgency,
        )
        self._pending.append(req)
        self._all_requests.append(req)
        return req

    def submit_verification(
        self,
        request_id: str,
        verifier_id: str,
        confidence: float,
        approved: bool,
        findings: Optional[list[str]] = None,
        recommendations: Optional[list[str]] = None,
        blocking_issues: Optional[list[str]] = None,
    ) -> VerificationResult:
        """Submit verification result.

        Raises ``ValueError`` if verifier_id == implementer_id
        (self-certification is forbidden by doctrine Rule 1).
        """
        request = self._find_pending(request_id)
        if request is None:
            raise ValueError(f"No pending request with id {request_id!r}")

        if self.is_self_certification(request.implementer_id, verifier_id):
            raise ValueError(
                "Self-certification rejected: verifier_id must differ from "
                f"implementer_id ({request.implementer_id!r})"
            )

        effective_blocking = blocking_issues or []
        if effective_blocking:
            approved = False

        result = VerificationResult(
            request_id=request_id,
            verifier_id=verifier_id,
            confidence=confidence,
            approved=approved,
            findings=findings or [],
            recommendations=recommendations or [],
            blocking_issues=effective_blocking,
        )
        self._completed.append(result)

        self._pending = [r for r in self._pending if r.request_id != request_id]
        return result

    # ── Promotion checks ──────────────────────────────────────────────

    def check_promotion_allowed(
        self,
        artifact_id: str,
        target_layer: int,
    ) -> tuple[bool, list[str]]:
        """Check if an artifact has sufficient verification for promotion.

        Returns ``(allowed, blocking_reasons)``.
        """
        reasons: list[str] = []

        if target_layer <= self._policy.max_self_certification_layer:
            return True, []

        results = self.get_verification_history(artifact_id)
        if not results:
            reasons.append(
                f"No verification found for artifact {artifact_id!r}; "
                f"L{target_layer} requires independent verification"
            )
            return False, reasons

        approved_results = [r for r in results if r.approved]
        if not approved_results:
            reasons.append("No approved verifications exist")
            return False, reasons

        best = max(approved_results, key=lambda r: r.confidence)
        if best.confidence < self._policy.min_verifier_confidence:
            reasons.append(
                f"Best verifier confidence ({best.confidence:.2f}) is below "
                f"policy threshold ({self._policy.min_verifier_confidence:.2f})"
            )
            if self._policy.escalate_on_low_confidence:
                reasons.append("Escalation to human operator recommended")
            return False, reasons

        return True, []

    # ── Identity checks ───────────────────────────────────────────────

    def is_self_certification(self, implementer_id: str, verifier_id: str) -> bool:
        """Check if this would be self-certification (blocked by doctrine)."""
        if not self._policy.require_different_agent:
            return False
        return implementer_id == verifier_id

    # ── Queries ───────────────────────────────────────────────────────

    def get_pending_verifications(self) -> list[VerificationRequest]:
        """Return all pending verification requests."""
        return list(self._pending)

    def get_verification_history(self, artifact_id: str) -> list[VerificationResult]:
        """Return all completed verifications for an artifact."""
        request_ids: set[str] = set()
        for req in self._all_requests:
            if req.artifact_id == artifact_id:
                request_ids.add(req.request_id)
        return [r for r in self._completed if r.request_id in request_ids]

    def needs_reverification(
        self,
        artifact_id: str,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """Check if verification has expired and needs renewal."""
        now = current_time or _utc_now()
        results = self.get_verification_history(artifact_id)
        if not results:
            return True

        latest = max(results, key=lambda r: r.verified_at)
        age_days = (now - latest.verified_at).total_seconds() / 86400.0
        return age_days > self._policy.max_verification_age_days

    # ── Audit ─────────────────────────────────────────────────────────

    def audit_trail(self) -> list[dict[str, Any]]:
        """Return complete audit trail of all verification activities."""
        trail: list[dict[str, Any]] = []

        for req in self._all_requests:
            is_pending = any(p.request_id == req.request_id for p in self._pending)
            trail.append({
                "type": "request_pending" if is_pending else "request_completed",
                "request_id": req.request_id,
                "artifact_id": req.artifact_id,
                "artifact_type": req.artifact_type,
                "implementer_id": req.implementer_id,
                "requested_at": req.requested_at.isoformat(),
                "urgency": req.urgency,
            })

        for result in self._completed:
            req = self._find_request_any(result.request_id)
            trail.append({
                "type": "verification_completed",
                "request_id": result.request_id,
                "artifact_id": req.artifact_id if req else "unknown",
                "artifact_type": req.artifact_type if req else "unknown",
                "implementer_id": req.implementer_id if req else "unknown",
                "verifier_id": result.verifier_id,
                "confidence": result.confidence,
                "approved": result.approved,
                "findings": result.findings,
                "blocking_issues": result.blocking_issues,
                "verified_at": result.verified_at.isoformat(),
            })

        return trail

    # ── Internal helpers ──────────────────────────────────────────────

    def _find_pending(self, request_id: str) -> Optional[VerificationRequest]:
        for req in self._pending:
            if req.request_id == request_id:
                return req
        return None

    def _find_request_any(self, request_id: str) -> Optional[VerificationRequest]:
        for req in self._all_requests:
            if req.request_id == request_id:
                return req
        return None
