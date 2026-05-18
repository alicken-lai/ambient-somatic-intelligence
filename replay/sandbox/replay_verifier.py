"""Replay Verifier — governance verification for the replay sandbox.

Wraps :class:`ConfidenceValidator` to verify replay promotions against
governance rules without touching any production verification state.
Blocked promotions are recorded but never propagated.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from governance.doctrine.confidence_validation import (
    ConfidenceValidator,
    VerificationPolicy,
    VerificationRequest,
    VerificationResult,
)
from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.promotion_engine import PromotionCandidate

from .replay_config import ReplayConfig


@dataclass
class ReplayVerificationRecord:
    """Immutable record of a verification decision during replay."""

    candidate: PromotionCandidate
    request: VerificationRequest
    result: VerificationResult | None
    allowed: bool
    blocking_reasons: list[str]
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate.candidate_id,
            "entry_id": self.candidate.entry_id,
            "source_layer": self.candidate.source_layer.value,
            "target_layer": self.candidate.target_layer.value,
            "request": self.request.to_dict(),
            "result": self.result.to_dict() if self.result else None,
            "allowed": self.allowed,
            "blocking_reasons": self.blocking_reasons,
            "verified_at": self.verified_at.isoformat(),
        }


class ReplayVerifier:
    """Sandboxed governance verifier for replay promotions.

    Maintains its own :class:`ConfidenceValidator` instance that is
    completely independent of production.  Every verification decision
    is recorded for post-replay auditing.

    When ``auto_approve_for_replay`` is enabled in the config, the
    verifier will synthesise approvals for candidates that would
    otherwise block on missing verification.
    """

    def __init__(
        self,
        config: ReplayConfig,
        policy: VerificationPolicy | None = None,
    ) -> None:
        self._config = config
        self._policy = policy or VerificationPolicy()
        self._validator = ConfidenceValidator(self._policy)
        self._records: list[ReplayVerificationRecord] = []
        self._audit: list[dict[str, Any]] = []
        self._id_counter: int = 0

    # ── Verification ─────────────────────────────────────────────────

    def verify_promotion(
        self,
        candidate: PromotionCandidate,
        implementer_id: str = "replay-engine",
        verifier_id: str | None = None,
    ) -> ReplayVerificationRecord:
        """Verify whether a promotion candidate passes governance rules.

        Steps:
          1. Create a verification request.
          2. If ``auto_approve_for_replay`` and no explicit verifier,
             synthesise a verifier and submit an approval.
          3. Check promotion allowed via the validator.
          4. Record and return the decision.
        """
        target_layer = candidate.target_layer.value

        req = self._validator.request_verification(
            artifact_id=candidate.entry_id,
            artifact_type="promotion_proposal",
            implementer_id=implementer_id,
            context={
                "candidate_id": candidate.candidate_id,
                "source_layer": candidate.source_layer.value,
                "target_layer": target_layer,
                "confidence": candidate.confidence,
            },
        )

        result: VerificationResult | None = None

        effective_verifier = verifier_id
        if not effective_verifier and self._config.auto_approve_for_replay:
            effective_verifier = f"replay-verifier-{self._next_id()}"

        if effective_verifier:
            try:
                result = self._validator.submit_verification(
                    request_id=req.request_id,
                    verifier_id=effective_verifier,
                    confidence=candidate.confidence,
                    approved=True,
                    findings=["Auto-approved in replay sandbox"],
                )
            except ValueError:
                result = None

        allowed, blocking_reasons = self._validator.check_promotion_allowed(
            artifact_id=candidate.entry_id,
            target_layer=target_layer,
        )

        if not self._config.enforce_governance:
            allowed = True
            blocking_reasons = []

        record = ReplayVerificationRecord(
            candidate=candidate,
            request=req,
            result=result,
            allowed=allowed,
            blocking_reasons=blocking_reasons,
        )
        self._records.append(record)

        self._audit.append({
            "action": "verify_promotion",
            "candidate_id": candidate.candidate_id,
            "entry_id": candidate.entry_id,
            "target_layer": target_layer,
            "allowed": allowed,
            "blocking_reasons": blocking_reasons,
            "auto_approved": bool(
                effective_verifier
                and self._config.auto_approve_for_replay
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return record

    def batch_verify(
        self,
        candidates: list[PromotionCandidate],
        implementer_id: str = "replay-engine",
    ) -> list[ReplayVerificationRecord]:
        """Verify a batch of candidates and return all records."""
        return [
            self.verify_promotion(c, implementer_id=implementer_id)
            for c in candidates
        ]

    # ── Query ─────────────────────────────────────────────────────────

    @property
    def records(self) -> list[ReplayVerificationRecord]:
        return list(self._records)

    @property
    def allowed_count(self) -> int:
        return sum(1 for r in self._records if r.allowed)

    @property
    def blocked_count(self) -> int:
        return sum(1 for r in self._records if not r.allowed)

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit)

    def get_blocked_promotions(self) -> list[ReplayVerificationRecord]:
        return [r for r in self._records if not r.allowed]

    def get_allowed_promotions(self) -> list[ReplayVerificationRecord]:
        return [r for r in self._records if r.allowed]

    def export_results(self) -> dict[str, Any]:
        return {
            "total_verifications": len(self._records),
            "allowed": self.allowed_count,
            "blocked": self.blocked_count,
            "records": [r.to_dict() for r in self._records],
            "governance_audit": self._validator.audit_trail(),
            "audit_log": self._audit,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    def _next_id(self) -> str:
        if self._config.deterministic_ids:
            self._id_counter += 1
            return f"{self._id_counter:06d}"
        return uuid.uuid4().hex[:12]
