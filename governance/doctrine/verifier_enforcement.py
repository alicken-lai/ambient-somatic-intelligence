"""Verifier enforcement for ontology promotions.

Ensures every promotion beyond L1 is independently verified by a
different entity than the promoter.  Implements the core invariant
from the Independent Verification Doctrine:

    promoter_id != verifier_id

Design anchors:
  - Aligns with ``VerificationPolicy`` thresholds in confidence_validation.py
  - Uses ``MemoryLayer`` from memory.ontology.layer_definition
  - Produces immutable ``VerificationRecord`` entries for the audit trail
  - Composable with PromotionChainValidator (promotion_chain_validator.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class VerificationRecord:
    """Immutable record of a single verification decision."""

    verification_id: str
    promotion_id: str
    promoter_id: str
    verifier_id: str
    source_level: str
    target_level: str
    confidence_assessment: float
    contradiction_found: bool
    contradictions: list[str]
    rationale: str
    decision: str  # APPROVED / REJECTED / NEEDS_REVIEW
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "promotion_id": self.promotion_id,
            "promoter_id": self.promoter_id,
            "verifier_id": self.verifier_id,
            "source_level": self.source_level,
            "target_level": self.target_level,
            "confidence_assessment": round(self.confidence_assessment, 6),
            "contradiction_found": self.contradiction_found,
            "contradictions": list(self.contradictions),
            "rationale": self.rationale,
            "decision": self.decision,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationRecord:
        return cls(
            verification_id=data["verification_id"],
            promotion_id=data["promotion_id"],
            promoter_id=data["promoter_id"],
            verifier_id=data["verifier_id"],
            source_level=data["source_level"],
            target_level=data["target_level"],
            confidence_assessment=data["confidence_assessment"],
            contradiction_found=data["contradiction_found"],
            contradictions=data.get("contradictions", []),
            rationale=data["rationale"],
            decision=data["decision"],
            timestamp=data["timestamp"],
        )


@dataclass
class PromotionRequest:
    """Lightweight representation of a promotion that needs verification.

    Designed so callers can build this from a ``PromotionCandidate``
    (promotion_engine.py) without tight coupling.
    """

    promotion_id: str
    entry_id: str
    promoter_id: str
    source_level: str      # e.g. "L2_INSTINCT"
    target_level: str      # e.g. "L3_SKILL"
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)
    domain: str = ""


@dataclass
class ContradictionResult:
    """Output of a contradiction scan."""

    contradiction_score: float          # 0.0 = none, 1.0 = total
    contradictions_found: list[str]
    evidence_examined: int
    recency_weighted: bool


# ---------------------------------------------------------------------------
# Core enforcement
# ---------------------------------------------------------------------------

VALID_DECISIONS = frozenset({"APPROVED", "REJECTED", "NEEDS_REVIEW"})

# Layers where self-certification is acceptable (L1 only, per doctrine).
SELF_CERT_ALLOWED_LEVELS = frozenset({"L1_EPISODIC"})


class VerifierEnforcement:
    """Enforces independent verification for all ontology promotions.

    Core invariant: promoter_id != verifier_id

    Responsibilities:
      1. Identity separation — block self-certification
      2. Confidence validation — verifier must independently assess confidence
      3. Contradiction scan — check for contradicting evidence before approval
      4. Rationale requirement — every verification needs written rationale
      5. Verification record — immutable record of every decision
    """

    def __init__(
        self,
        min_verifier_confidence: float = 0.7,
        l4_min_verifier_confidence: float = 0.8,
        historical_evidence: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self._min_confidence = min_verifier_confidence
        self._l4_min_confidence = l4_min_verifier_confidence
        self._records: list[VerificationRecord] = []
        self._historical_evidence: list[dict[str, Any]] = (
            historical_evidence or []
        )

    # ── Identity separation ───────────────────────────────────────────

    def is_self_certification(
        self, promoter_id: str, verifier_id: str
    ) -> bool:
        """Return True if the same entity is both promoter and verifier."""
        return promoter_id == verifier_id

    # ── Confidence validation ─────────────────────────────────────────

    def validate_verifier_confidence(
        self,
        confidence: float,
        target_level: str,
    ) -> tuple[bool, str]:
        """Check whether verifier confidence meets the threshold.

        L3→L4 promotions require >= 0.8 (per doctrine).
        All others require >= 0.7 (default policy).

        Returns (passes, reason).
        """
        threshold = (
            self._l4_min_confidence
            if target_level == "L4_STRATEGIC"
            else self._min_confidence
        )
        if confidence < threshold:
            return False, (
                f"Verifier confidence {confidence:.2f} below threshold "
                f"{threshold:.2f} for target {target_level}"
            )
        return True, ""

    # ── Contradiction scan ────────────────────────────────────────────

    def scan_contradictions(
        self,
        promotion_request: PromotionRequest,
        additional_evidence: Optional[list[dict[str, Any]]] = None,
    ) -> ContradictionResult:
        """Scan historical evidence for contradictions.

        Recent contradictions are weighted more heavily than old ones.
        Returns a score in [0.0, 1.0].
        """
        evidence_pool = list(self._historical_evidence)
        if additional_evidence:
            evidence_pool.extend(additional_evidence)

        domain = promotion_request.domain
        entry_id = promotion_request.entry_id

        relevant: list[dict[str, Any]] = []
        for ev in evidence_pool:
            if self._evidence_matches(ev, domain, entry_id):
                relevant.append(ev)

        if not relevant:
            return ContradictionResult(
                contradiction_score=0.0,
                contradictions_found=[],
                evidence_examined=len(evidence_pool),
                recency_weighted=True,
            )

        now = _utc_now()
        weighted_contradiction = 0.0
        total_weight = 0.0
        found: list[str] = []

        for ev in relevant:
            weight = self._recency_weight(ev, now)
            total_weight += weight

            if ev.get("contradicts", False):
                weighted_contradiction += weight
                desc = ev.get("description", ev.get("event", "unknown"))
                found.append(str(desc))

        score = (
            weighted_contradiction / total_weight if total_weight > 0 else 0.0
        )
        score = max(0.0, min(1.0, score))

        return ContradictionResult(
            contradiction_score=score,
            contradictions_found=found,
            evidence_examined=len(relevant),
            recency_weighted=True,
        )

    # ── Rationale requirement ─────────────────────────────────────────

    @staticmethod
    def validate_rationale(rationale: str) -> tuple[bool, str]:
        """Ensure a non-trivial rationale is provided."""
        stripped = rationale.strip() if rationale else ""
        if not stripped:
            return False, "Rationale is required for every verification"
        if len(stripped) < 10:
            return False, (
                f"Rationale too short ({len(stripped)} chars); "
                "provide meaningful justification"
            )
        return True, ""

    # ── Unified verify entry point ────────────────────────────────────

    def verify(
        self,
        promotion_request: PromotionRequest,
        verifier_id: str,
        confidence_assessment: float,
        rationale: str,
        additional_evidence: Optional[list[dict[str, Any]]] = None,
    ) -> VerificationRecord:
        """Run all enforcement checks and produce a VerificationRecord.

        Checks in order:
          1. Identity separation (promoter != verifier)
          2. Confidence threshold
          3. Contradiction scan
          4. Rationale non-empty
        If any check fails the decision is REJECTED (or NEEDS_REVIEW
        for borderline confidence).
        """
        pr = promotion_request
        blocking: list[str] = []

        # 1 — Self-certification
        if pr.source_level not in SELF_CERT_ALLOWED_LEVELS:
            if self.is_self_certification(pr.promoter_id, verifier_id):
                blocking.append(
                    f"Self-certification blocked: promoter_id "
                    f"({pr.promoter_id!r}) == verifier_id ({verifier_id!r})"
                )

        # 2 — Confidence
        conf_ok, conf_reason = self.validate_verifier_confidence(
            confidence_assessment, pr.target_level
        )
        if not conf_ok:
            blocking.append(conf_reason)

        # 3 — Contradiction scan
        contra = self.scan_contradictions(pr, additional_evidence)

        if contra.contradiction_score >= 0.5:
            blocking.append(
                f"High contradiction score ({contra.contradiction_score:.2f}): "
                + "; ".join(contra.contradictions_found[:3])
            )

        # 4 — Rationale
        rat_ok, rat_reason = self.validate_rationale(rationale)
        if not rat_ok:
            blocking.append(rat_reason)

        # Decide
        if blocking:
            decision = "REJECTED"
        elif contra.contradiction_score >= 0.2:
            decision = "NEEDS_REVIEW"
        else:
            decision = "APPROVED"

        record = VerificationRecord(
            verification_id=_new_id(),
            promotion_id=pr.promotion_id,
            promoter_id=pr.promoter_id,
            verifier_id=verifier_id,
            source_level=pr.source_level,
            target_level=pr.target_level,
            confidence_assessment=confidence_assessment,
            contradiction_found=contra.contradiction_score > 0.0,
            contradictions=contra.contradictions_found,
            rationale=rationale if rat_ok else f"[INVALID] {rationale}",
            decision=decision,
            timestamp=_utc_now().isoformat(),
        )
        self._records.append(record)
        return record

    # ── Queries ───────────────────────────────────────────────────────

    def get_records(
        self, promotion_id: Optional[str] = None
    ) -> list[VerificationRecord]:
        """Return verification records, optionally filtered by promotion."""
        if promotion_id is None:
            return list(self._records)
        return [r for r in self._records if r.promotion_id == promotion_id]

    def get_blocked_records(self) -> list[VerificationRecord]:
        """Return all records where the decision was REJECTED."""
        return [r for r in self._records if r.decision == "REJECTED"]

    def get_self_certification_blocks(self) -> list[VerificationRecord]:
        """Return records blocked specifically for self-certification."""
        return [
            r for r in self._records
            if r.decision == "REJECTED"
            and r.promoter_id == r.verifier_id
        ]

    def audit_trail(self) -> list[dict[str, Any]]:
        """Return the complete verification audit trail as dicts."""
        return [r.to_dict() for r in self._records]

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _evidence_matches(
        evidence: dict[str, Any], domain: str, entry_id: str
    ) -> bool:
        """Check if a piece of evidence is relevant to the promotion."""
        ev_domain = evidence.get("domain", "")
        ev_entry = evidence.get("entry_id", "")
        ev_related = evidence.get("related_entries", [])

        if ev_entry and ev_entry == entry_id:
            return True
        if entry_id in ev_related:
            return True
        if domain and ev_domain and ev_domain == domain:
            return True
        return False

    @staticmethod
    def _recency_weight(evidence: dict[str, Any], now: datetime) -> float:
        """Weight recent evidence more heavily (exponential decay)."""
        ts_str = evidence.get("timestamp", "")
        if not ts_str:
            return 0.5  # unknown age → neutral weight

        try:
            ts = datetime.fromisoformat(str(ts_str))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return 0.5

        age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
        import math
        return math.exp(-0.05 * age_days)  # half-life ≈ 14 days
