"""Promotion verification gate — blocks promotions without independent verification.

This module is the enforcement boundary between the promotion engine
(``memory.ontology.promotion_engine``) and the rest of the system.  No
promotion proceeds unless it passes through ``PromotionVerificationGate``.

Blocks:
  - Missing verifier
  - Self-verification (promoter == verifier)
  - Low verifier confidence
  - Contradictory evidence found by verifier
  - Missing rationale

Composable with:
  - ``PromotionChainValidator`` (memory/ontology/promotion_chain_validator.py)
  - ``ConfidenceValidator`` (governance/doctrine/confidence_validation.py)
  - ``VerifierEnforcement`` (governance/doctrine/verifier_enforcement.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .verifier_enforcement import (
    ContradictionResult,
    PromotionRequest,
    VerificationRecord,
    VerifierEnforcement,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


# ---------------------------------------------------------------------------
# Gate result types
# ---------------------------------------------------------------------------

@dataclass
class GateVerdict:
    """Outcome of the promotion verification gate."""

    allowed: bool
    decision: str                # APPROVED / REJECTED / NEEDS_REVIEW
    blocking_reasons: list[str]
    verification_record: Optional[VerificationRecord]
    contradiction_result: Optional[ContradictionResult]
    gate_id: str = field(default_factory=_new_id)
    timestamp: str = field(
        default_factory=lambda: _utc_now().isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "allowed": self.allowed,
            "decision": self.decision,
            "blocking_reasons": list(self.blocking_reasons),
            "verification_record": (
                self.verification_record.to_dict()
                if self.verification_record
                else None
            ),
            "contradiction_result": (
                {
                    "score": self.contradiction_result.contradiction_score,
                    "contradictions": self.contradiction_result.contradictions_found,
                    "evidence_examined": self.contradiction_result.evidence_examined,
                }
                if self.contradiction_result
                else None
            ),
            "timestamp": self.timestamp,
        }


@dataclass
class SelfCertificationReport:
    """Detailed report when self-certification is detected and blocked."""

    report_id: str
    promotion_id: str
    promoter_id: str
    attempted_verifier_id: str
    source_level: str
    target_level: str
    entry_id: str
    blocked_at: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "promotion_id": self.promotion_id,
            "promoter_id": self.promoter_id,
            "attempted_verifier_id": self.attempted_verifier_id,
            "source_level": self.source_level,
            "target_level": self.target_level,
            "entry_id": self.entry_id,
            "blocked_at": self.blocked_at,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Levels that allow self-certification (L1 only, per doctrine)
# ---------------------------------------------------------------------------

_SELF_CERT_ALLOWED = frozenset({"L1_EPISODIC"})


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

class PromotionVerificationGate:
    """No promotion proceeds without independent verification.

    Usage::

        gate = PromotionVerificationGate()
        verdict = gate.verify_promotion(promotion_request, verifier_id,
                                        confidence, rationale)
        if verdict.allowed:
            # proceed with promotion
        else:
            # handle blocking_reasons

    The gate delegates core checks to ``VerifierEnforcement`` and adds
    its own gate-level policy (e.g. mandatory verifier presence).
    """

    def __init__(
        self,
        enforcement: Optional[VerifierEnforcement] = None,
        min_verifier_confidence: float = 0.7,
        contradiction_block_threshold: float = 0.5,
        contradiction_review_threshold: float = 0.2,
        historical_evidence: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self._enforcement = enforcement or VerifierEnforcement(
            min_verifier_confidence=min_verifier_confidence,
            historical_evidence=historical_evidence,
        )
        self._contradiction_block = contradiction_block_threshold
        self._contradiction_review = contradiction_review_threshold

        self._verdicts: list[GateVerdict] = []
        self._self_cert_reports: list[SelfCertificationReport] = []

    # ── Main entry point ──────────────────────────────────────────────

    def verify_promotion(
        self,
        promotion_request: PromotionRequest,
        verifier_id: Optional[str],
        confidence: float = 0.0,
        rationale: str = "",
        additional_evidence: Optional[list[dict[str, Any]]] = None,
    ) -> GateVerdict:
        """Run all gate checks and return a verdict.

        Checks (in order):
          1. Verifier presence — a verifier_id must be supplied
          2. Self-certification — promoter_id != verifier_id
          3. Delegate to VerifierEnforcement.verify() which checks:
             a. Confidence threshold
             b. Contradiction scan
             c. Rationale adequacy

        All checks run to completion so the caller gets a full list of
        blocking reasons (fail-open is never permitted).
        """
        pr = promotion_request
        blocking: list[str] = []
        contradiction: Optional[ContradictionResult] = None
        verification: Optional[VerificationRecord] = None

        # --- Gate-level pre-checks ---

        # 1. Missing verifier
        if not verifier_id:
            blocking.append(
                "Verifier ID is required; no promotion without "
                "independent verification"
            )
            return self._record_verdict(
                allowed=False,
                decision="REJECTED",
                blocking=blocking,
                verification=None,
                contradiction=None,
            )

        # 2. Self-certification
        if pr.source_level not in _SELF_CERT_ALLOWED:
            if self._enforcement.is_self_certification(
                pr.promoter_id, verifier_id
            ):
                report = self._create_self_cert_report(pr, verifier_id)
                self._self_cert_reports.append(report)
                blocking.append(
                    f"Self-certification blocked: promoter "
                    f"({pr.promoter_id!r}) cannot verify their own "
                    f"promotion (verifier: {verifier_id!r})"
                )
                return self._record_verdict(
                    allowed=False,
                    decision="REJECTED",
                    blocking=blocking,
                    verification=None,
                    contradiction=None,
                )

        # --- Delegate to VerifierEnforcement ---

        verification = self._enforcement.verify(
            promotion_request=pr,
            verifier_id=verifier_id,
            confidence_assessment=confidence,
            rationale=rationale,
            additional_evidence=additional_evidence,
        )

        # Pull contradiction result from the enforcement run
        contradiction = self._enforcement.scan_contradictions(
            pr, additional_evidence
        )

        if verification.decision == "REJECTED":
            blocking.extend(self._extract_blocking_reasons(verification))

        allowed = verification.decision == "APPROVED"
        verdict = self._record_verdict(
            allowed=allowed,
            decision=verification.decision,
            blocking=blocking,
            verification=verification,
            contradiction=contradiction,
        )
        return verdict

    # ── Batch gate (for PromotionChainValidator interop) ──────────────

    def gate_candidates(
        self,
        candidates: list[dict[str, Any]],
        verifier_id: Optional[str],
        confidence: float = 0.0,
        rationale: str = "",
    ) -> list[GateVerdict]:
        """Run the gate over a batch of promotion candidates.

        Each candidate dict must contain at least: promotion_id,
        entry_id, promoter_id, source_level, target_level, confidence.
        """
        verdicts: list[GateVerdict] = []
        for cand in candidates:
            pr = PromotionRequest(
                promotion_id=cand.get("promotion_id", cand.get("candidate_id", _new_id())),
                entry_id=cand.get("entry_id", ""),
                promoter_id=cand.get("promoter_id", ""),
                source_level=cand.get("source_level", ""),
                target_level=cand.get("target_level", ""),
                confidence=cand.get("confidence", 0.0),
                evidence=cand.get("evidence", {}),
                domain=cand.get("domain", ""),
            )
            v = self.verify_promotion(
                pr, verifier_id, confidence, rationale
            )
            verdicts.append(v)
        return verdicts

    # ── Query methods ─────────────────────────────────────────────────

    def get_all_verdicts(self) -> list[GateVerdict]:
        return list(self._verdicts)

    def get_blocked_verdicts(self) -> list[GateVerdict]:
        return [v for v in self._verdicts if not v.allowed]

    def get_approved_verdicts(self) -> list[GateVerdict]:
        return [v for v in self._verdicts if v.allowed]

    def get_self_certification_reports(self) -> list[SelfCertificationReport]:
        return list(self._self_cert_reports)

    def get_verification_records(self) -> list[VerificationRecord]:
        """Proxy to the underlying enforcement's records."""
        return self._enforcement.get_records()

    def audit_trail(self) -> list[dict[str, Any]]:
        """Full audit trail of all gate decisions."""
        return [v.to_dict() for v in self._verdicts]

    # ── Metrics ───────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        total = len(self._verdicts)
        approved = sum(1 for v in self._verdicts if v.allowed)
        rejected = sum(
            1 for v in self._verdicts if v.decision == "REJECTED"
        )
        needs_review = sum(
            1 for v in self._verdicts if v.decision == "NEEDS_REVIEW"
        )
        return {
            "total_verifications": total,
            "approved": approved,
            "rejected": rejected,
            "needs_review": needs_review,
            "self_certification_blocks": len(self._self_cert_reports),
            "approval_rate": approved / total if total else 0.0,
        }

    # ── Internal ──────────────────────────────────────────────────────

    def _record_verdict(
        self,
        *,
        allowed: bool,
        decision: str,
        blocking: list[str],
        verification: Optional[VerificationRecord],
        contradiction: Optional[ContradictionResult],
    ) -> GateVerdict:
        verdict = GateVerdict(
            allowed=allowed,
            decision=decision,
            blocking_reasons=blocking,
            verification_record=verification,
            contradiction_result=contradiction,
        )
        self._verdicts.append(verdict)
        return verdict

    @staticmethod
    def _create_self_cert_report(
        pr: PromotionRequest, verifier_id: str
    ) -> SelfCertificationReport:
        return SelfCertificationReport(
            report_id=_new_id(),
            promotion_id=pr.promotion_id,
            promoter_id=pr.promoter_id,
            attempted_verifier_id=verifier_id,
            source_level=pr.source_level,
            target_level=pr.target_level,
            entry_id=pr.entry_id,
            blocked_at=_utc_now().isoformat(),
            reason=(
                f"Promoter ({pr.promoter_id!r}) attempted to verify their "
                f"own promotion ({pr.promotion_id!r}). Self-certification "
                f"is forbidden for {pr.source_level} → {pr.target_level} "
                f"promotions per the Independent Verification Doctrine."
            ),
        )

    @staticmethod
    def _extract_blocking_reasons(record: VerificationRecord) -> list[str]:
        """Pull human-readable blocking reasons from a rejected record."""
        reasons: list[str] = []
        if record.promoter_id == record.verifier_id:
            reasons.append("Self-certification")
        if record.contradiction_found and record.contradictions:
            reasons.append(
                f"Contradictions: {'; '.join(record.contradictions[:3])}"
            )
        if not record.rationale or record.rationale.startswith("[INVALID]"):
            reasons.append("Missing or invalid rationale")
        return reasons
