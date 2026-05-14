"""Promotion Engine — promotes local knowledge into global doctrine.

All promotions are PROPOSED only and require explicit governance approval.
Every decision is auditable and reversible.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .confidence_model import ConfidenceModel
from .layer_definition import MemoryLayer
from .promotion_rules import PromotionRule, check_promotion_eligibility


@dataclass
class PromotionCandidate:
    entry_id: str
    source_layer: MemoryLayer
    target_layer: MemoryLayer
    confidence: float
    evidence: dict[str, Any]
    eligible: bool
    blocking_reasons: list[str]
    proposed_at: datetime
    candidate_id: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id:
            self.candidate_id = uuid.uuid4().hex[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "entry_id": self.entry_id,
            "source_layer": self.source_layer.value,
            "target_layer": self.target_layer.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "eligible": self.eligible,
            "blocking_reasons": list(self.blocking_reasons),
            "proposed_at": self.proposed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromotionCandidate:
        return cls(
            candidate_id=data.get("candidate_id", ""),
            entry_id=data["entry_id"],
            source_layer=MemoryLayer(data["source_layer"]),
            target_layer=MemoryLayer(data["target_layer"]),
            confidence=data["confidence"],
            evidence=data["evidence"],
            eligible=data["eligible"],
            blocking_reasons=data.get("blocking_reasons", []),
            proposed_at=datetime.fromisoformat(data["proposed_at"]),
        )


@dataclass
class PromotionResult:
    candidate: PromotionCandidate
    approved: bool
    new_entry_id: str | None
    governance_decision_id: str | None
    verifier_id: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "approved": self.approved,
            "new_entry_id": self.new_entry_id,
            "governance_decision_id": self.governance_decision_id,
            "verifier_id": self.verifier_id,
            "reason": self.reason,
        }


def _build_evidence(entry: Any) -> dict[str, Any]:
    evidence: dict[str, Any] = {"confidence": entry.confidence}
    if hasattr(entry, "access_count"):
        evidence["occurrence_count"] = entry.access_count
    if hasattr(entry, "occurrence_count"):
        evidence["occurrence_count"] = entry.occurrence_count
    if hasattr(entry, "execution_count"):
        evidence["occurrence_count"] = entry.execution_count
    if hasattr(entry, "success_rate") and callable(entry.success_rate):
        evidence["success_rate"] = entry.success_rate()
    if hasattr(entry, "contextual_applicability"):
        evidence["cross_contexts"] = list(entry.contextual_applicability)
    if hasattr(entry, "contexts_validated"):
        evidence["cross_contexts"] = list(entry.contexts_validated)
    return evidence


class PromotionEngine:
    """Scans, proposes, approves/rejects, and rolls back promotions."""

    def __init__(
        self,
        rules: list[PromotionRule],
        confidence_model: ConfidenceModel,
    ) -> None:
        self._rules = rules
        self._confidence_model = confidence_model
        self._pending: dict[str, PromotionCandidate] = {}
        self._audit: list[dict[str, Any]] = []
        self._results: dict[str, PromotionResult] = {}

    def _rule_for_layer(self, layer: MemoryLayer) -> PromotionRule | None:
        for r in self._rules:
            if r.source_layer == layer:
                return r
        return None

    def scan_candidates(
        self, entries: list[Any], layer: MemoryLayer
    ) -> list[PromotionCandidate]:
        """Find all entries eligible for promotion from the given layer."""
        rule = self._rule_for_layer(layer)
        if rule is None:
            return []

        candidates: list[PromotionCandidate] = []
        for entry in entries:
            if entry.layer != layer:
                continue
            eligible, reasons = check_promotion_eligibility(entry, rule)
            candidate = PromotionCandidate(
                entry_id=entry.entry_id,
                source_layer=layer,
                target_layer=rule.target_layer,
                confidence=entry.confidence,
                evidence=_build_evidence(entry),
                eligible=eligible,
                blocking_reasons=reasons,
                proposed_at=datetime.now(timezone.utc),
            )
            candidates.append(candidate)
        return candidates

    def propose_promotion(
        self, candidate: PromotionCandidate
    ) -> PromotionCandidate:
        """Register a promotion proposal (does NOT auto-promote)."""
        self._pending[candidate.candidate_id] = candidate
        self._audit.append(
            {
                "action": "proposed",
                "candidate_id": candidate.candidate_id,
                "entry_id": candidate.entry_id,
                "source_layer": candidate.source_layer.value,
                "target_layer": candidate.target_layer.value,
                "eligible": candidate.eligible,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return candidate

    def approve_promotion(
        self,
        candidate_id: str,
        governance_decision_id: str,
        verifier_id: str | None = None,
    ) -> PromotionResult:
        """Approve and execute a promotion. Requires governance approval."""
        candidate = self._pending.get(candidate_id)
        if candidate is None:
            return PromotionResult(
                candidate=PromotionCandidate(
                    entry_id="",
                    source_layer=MemoryLayer.L1_EPISODIC,
                    target_layer=MemoryLayer.L2_INSTINCT,
                    confidence=0.0,
                    evidence={},
                    eligible=False,
                    blocking_reasons=["Candidate not found"],
                    proposed_at=datetime.now(timezone.utc),
                    candidate_id=candidate_id,
                ),
                approved=False,
                new_entry_id=None,
                governance_decision_id=governance_decision_id,
                verifier_id=verifier_id,
                reason="Candidate not found",
            )

        if not candidate.eligible:
            result = PromotionResult(
                candidate=candidate,
                approved=False,
                new_entry_id=None,
                governance_decision_id=governance_decision_id,
                verifier_id=verifier_id,
                reason=f"Candidate not eligible: {candidate.blocking_reasons}",
            )
            self._record_decision(result, "rejected_ineligible")
            return result

        if not governance_decision_id:
            result = PromotionResult(
                candidate=candidate,
                approved=False,
                new_entry_id=None,
                governance_decision_id=None,
                verifier_id=verifier_id,
                reason="Governance decision ID is required",
            )
            self._record_decision(result, "rejected_no_governance")
            return result

        if (
            candidate.target_layer == MemoryLayer.L4_STRATEGIC
            and not verifier_id
        ):
            result = PromotionResult(
                candidate=candidate,
                approved=False,
                new_entry_id=None,
                governance_decision_id=governance_decision_id,
                verifier_id=None,
                reason="L3→L4 promotion requires verifier_id",
            )
            self._record_decision(result, "rejected_no_verifier")
            return result

        new_entry_id = uuid.uuid4().hex[:12]
        result = PromotionResult(
            candidate=candidate,
            approved=True,
            new_entry_id=new_entry_id,
            governance_decision_id=governance_decision_id,
            verifier_id=verifier_id,
            reason="Promotion approved",
        )
        self._record_decision(result, "approved")
        self._results[candidate_id] = result
        del self._pending[candidate_id]
        return result

    def reject_promotion(
        self, candidate_id: str, reason: str
    ) -> PromotionResult:
        """Reject a promotion candidate."""
        candidate = self._pending.get(candidate_id)
        if candidate is None:
            return PromotionResult(
                candidate=PromotionCandidate(
                    entry_id="",
                    source_layer=MemoryLayer.L1_EPISODIC,
                    target_layer=MemoryLayer.L2_INSTINCT,
                    confidence=0.0,
                    evidence={},
                    eligible=False,
                    blocking_reasons=["Candidate not found"],
                    proposed_at=datetime.now(timezone.utc),
                    candidate_id=candidate_id,
                ),
                approved=False,
                new_entry_id=None,
                governance_decision_id=None,
                verifier_id=None,
                reason=reason,
            )

        result = PromotionResult(
            candidate=candidate,
            approved=False,
            new_entry_id=None,
            governance_decision_id=None,
            verifier_id=None,
            reason=reason,
        )
        self._record_decision(result, "rejected")
        del self._pending[candidate_id]
        return result

    def rollback_promotion(self, promotion_result: PromotionResult) -> bool:
        """Reverse a previously approved promotion."""
        if not promotion_result.approved:
            return False

        self._audit.append(
            {
                "action": "rollback",
                "candidate_id": promotion_result.candidate.candidate_id,
                "entry_id": promotion_result.candidate.entry_id,
                "new_entry_id": promotion_result.new_entry_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        promotion_result.approved = False
        promotion_result.reason = "Rolled back"
        return True

    def audit_log(self) -> list[dict[str, Any]]:
        """Return all promotion decisions as an audit trail."""
        return list(self._audit)

    def get_pending(self) -> list[PromotionCandidate]:
        """Return all pending promotion candidates."""
        return list(self._pending.values())

    def _record_decision(
        self, result: PromotionResult, action: str
    ) -> None:
        self._audit.append(
            {
                "action": action,
                "candidate_id": result.candidate.candidate_id,
                "entry_id": result.candidate.entry_id,
                "approved": result.approved,
                "governance_decision_id": result.governance_decision_id,
                "verifier_id": result.verifier_id,
                "reason": result.reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
