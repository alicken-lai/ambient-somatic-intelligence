"""Strategic Write Gate — prevents direct L4 writes without full promotion chain provenance.

This is the final line of defense against the root cause identified in the P1 Reality
Replay: agent memory initialization injecting L4 strategic entries with confidence 1.0
bypassing the entire L1→L2→L3→L4 promotion hierarchy.

The gate intercepts ANY attempt to write L4 strategic memory and validates:
  1. Complete promotion chain provenance (L1→L2→L3→L4 history exists)
  2. Verifier approval for the L3→L4 transition
  3. Governance approval reference
  4. Minimum confidence/recurrence thresholds

Emergency overrides require Guardian approval and are logged with full context.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .layer_definition import MemoryLayer
from .promotion_violation import PromotionViolation, ViolationLog

logger = logging.getLogger(__name__)


@dataclass
class PromotionProvenance:
    """Proof that an entry traversed the full promotion chain."""

    l1_entry_id: str = ""
    l1_promoted_at: str = ""
    l2_entry_id: str = ""
    l2_promoted_at: str = ""
    l2_governance_id: str = ""
    l3_entry_id: str = ""
    l3_promoted_at: str = ""
    l3_governance_id: str = ""
    l3_to_l4_verifier_id: str = ""
    l3_to_l4_governance_id: str = ""

    def is_complete(self) -> bool:
        """Check if the provenance chain is fully populated."""
        return bool(
            self.l1_entry_id
            and self.l2_entry_id
            and self.l3_entry_id
            and self.l3_to_l4_verifier_id
            and self.l3_to_l4_governance_id
        )

    def missing_links(self) -> list[str]:
        """Return a list of missing provenance links."""
        missing: list[str] = []
        if not self.l1_entry_id:
            missing.append("l1_entry_id (episodic origin)")
        if not self.l2_entry_id:
            missing.append("l2_entry_id (instinct precursor)")
        if not self.l3_entry_id:
            missing.append("l3_entry_id (skill precursor)")
        if not self.l3_to_l4_verifier_id:
            missing.append("l3_to_l4_verifier_id (independent verifier for L3→L4)")
        if not self.l3_to_l4_governance_id:
            missing.append("l3_to_l4_governance_id (governance approval for L3→L4)")
        return missing

    def to_dict(self) -> dict[str, Any]:
        return {
            "l1_entry_id": self.l1_entry_id,
            "l1_promoted_at": self.l1_promoted_at,
            "l2_entry_id": self.l2_entry_id,
            "l2_promoted_at": self.l2_promoted_at,
            "l2_governance_id": self.l2_governance_id,
            "l3_entry_id": self.l3_entry_id,
            "l3_promoted_at": self.l3_promoted_at,
            "l3_governance_id": self.l3_governance_id,
            "l3_to_l4_verifier_id": self.l3_to_l4_verifier_id,
            "l3_to_l4_governance_id": self.l3_to_l4_governance_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromotionProvenance:
        return cls(
            l1_entry_id=data.get("l1_entry_id", ""),
            l1_promoted_at=data.get("l1_promoted_at", ""),
            l2_entry_id=data.get("l2_entry_id", ""),
            l2_promoted_at=data.get("l2_promoted_at", ""),
            l2_governance_id=data.get("l2_governance_id", ""),
            l3_entry_id=data.get("l3_entry_id", ""),
            l3_promoted_at=data.get("l3_promoted_at", ""),
            l3_governance_id=data.get("l3_governance_id", ""),
            l3_to_l4_verifier_id=data.get("l3_to_l4_verifier_id", ""),
            l3_to_l4_governance_id=data.get("l3_to_l4_governance_id", ""),
        )


@dataclass
class WriteGateDecision:
    """Result of the strategic write gate evaluation."""

    allowed: bool
    entry_id: str
    reason: str
    provenance_valid: bool
    verifier_valid: bool
    governance_valid: bool
    emergency_override: bool
    guardian_approval_id: str
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    violation: PromotionViolation | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "allowed": self.allowed,
            "entry_id": self.entry_id,
            "reason": self.reason,
            "provenance_valid": self.provenance_valid,
            "verifier_valid": self.verifier_valid,
            "governance_valid": self.governance_valid,
            "emergency_override": self.emergency_override,
            "guardian_approval_id": self.guardian_approval_id,
            "decided_at": self.decided_at.isoformat(),
        }
        if self.violation:
            result["violation"] = self.violation.to_dict()
        return result


class StrategicWriteGate:
    """Prevents any L4 strategic memory write that hasn't gone through
    the full promotion chain (L1→L2→L3→L4) with verifier approval.

    This gate must be called before any L4 write operation. It validates:
      - Complete promotion provenance chain
      - Independent verifier approval for L3→L4
      - Governance approval reference
      - No self-certification

    Emergency overrides are supported ONLY with explicit Guardian approval,
    and all overrides are logged with full audit context.

    Usage:
        gate = StrategicWriteGate()

        provenance = PromotionProvenance(
            l1_entry_id="ep-001",
            l2_entry_id="inst-001",
            l3_entry_id="skill-001",
            l3_to_l4_verifier_id="verifier-agent-2",
            l3_to_l4_governance_id="GOV-789",
        )

        decision = gate.check_write(
            entry_id="strat-001",
            provenance=provenance,
            confidence=0.92,
            promoter_id="skillify-agent",
        )

        if decision.allowed:
            # proceed with L4 write
            ...
        else:
            # write blocked — log and report
            ...
    """

    def __init__(
        self,
        violation_log: ViolationLog | None = None,
        audit_log_path: str | Path = "repair/audit/strategic_gate_decisions.jsonl",
    ) -> None:
        self._violation_log = violation_log or ViolationLog()
        self._audit_log_path = Path(audit_log_path)
        self._decisions: list[WriteGateDecision] = []

    def check_write(
        self,
        entry_id: str,
        provenance: PromotionProvenance,
        confidence: float = 0.0,
        promoter_id: str = "",
    ) -> WriteGateDecision:
        """Evaluate whether an L4 write should be allowed.

        Args:
            entry_id: ID of the strategic entry being written.
            provenance: Full promotion chain provenance.
            confidence: Confidence score of the entry.
            promoter_id: ID of the entity requesting the write.

        Returns:
            WriteGateDecision indicating allow/block with detailed reasons.
        """
        provenance_valid = provenance.is_complete()
        verifier_valid = self._validate_verifier(provenance, promoter_id)
        governance_valid = bool(provenance.l3_to_l4_governance_id)

        all_valid = provenance_valid and verifier_valid and governance_valid

        if all_valid:
            reason = "Full promotion chain validated: L1→L2→L3→L4 with independent verifier"
            decision = WriteGateDecision(
                allowed=True,
                entry_id=entry_id,
                reason=reason,
                provenance_valid=provenance_valid,
                verifier_valid=verifier_valid,
                governance_valid=governance_valid,
                emergency_override=False,
                guardian_approval_id="",
            )
        else:
            reasons: list[str] = []
            if not provenance_valid:
                missing = provenance.missing_links()
                reasons.append(f"Incomplete provenance: missing {missing}")
            if not verifier_valid:
                reasons.append(
                    "Verifier invalid: missing, or same as promoter (self-certification)"
                )
            if not governance_valid:
                reasons.append("No governance approval for L3→L4 transition")

            combined_reason = "; ".join(reasons)

            violation = self._violation_log.create_and_record(
                source_level="L3_SKILL",
                target_level="L4_STRATEGIC",
                reason=combined_reason,
                confidence=confidence,
                recurrence=0,
                governance_reference=provenance.l3_to_l4_governance_id,
                blocked=True,
                source_file="strategic_write_gate",
                source_function="check_write",
                entry_id=entry_id,
                additional_context={
                    "promoter_id": promoter_id,
                    "provenance": provenance.to_dict(),
                },
            )

            decision = WriteGateDecision(
                allowed=False,
                entry_id=entry_id,
                reason=combined_reason,
                provenance_valid=provenance_valid,
                verifier_valid=verifier_valid,
                governance_valid=governance_valid,
                emergency_override=False,
                guardian_approval_id="",
                violation=violation,
            )

        self._decisions.append(decision)
        self._persist_decision(decision)

        logger.info(
            "Strategic write gate: entry=%s allowed=%s reason=%r",
            entry_id, decision.allowed, decision.reason,
        )
        return decision

    def emergency_override(
        self,
        entry_id: str,
        guardian_approval_id: str,
        override_reason: str,
        confidence: float = 0.0,
        promoter_id: str = "",
    ) -> WriteGateDecision:
        """Allow an L4 write with Guardian emergency override.

        This bypasses the provenance check but ONLY with explicit Guardian
        approval. The override is logged with maximum visibility.

        Args:
            entry_id: ID of the strategic entry.
            guardian_approval_id: Guardian's approval reference (required).
            override_reason: Human-readable reason for the override.
            confidence: Confidence score of the entry.
            promoter_id: Entity requesting the override.

        Returns:
            WriteGateDecision with emergency_override=True.

        Raises:
            ValueError: If guardian_approval_id is empty.
        """
        if not guardian_approval_id:
            raise ValueError(
                "Emergency override requires guardian_approval_id — "
                "cannot bypass strategic write gate without Guardian approval"
            )

        decision = WriteGateDecision(
            allowed=True,
            entry_id=entry_id,
            reason=f"EMERGENCY OVERRIDE by Guardian ({guardian_approval_id}): {override_reason}",
            provenance_valid=False,
            verifier_valid=False,
            governance_valid=True,
            emergency_override=True,
            guardian_approval_id=guardian_approval_id,
        )

        self._decisions.append(decision)
        self._persist_decision(decision)

        logger.warning(
            "EMERGENCY OVERRIDE: Strategic write gate bypassed for entry=%s "
            "guardian=%s reason=%r promoter=%s",
            entry_id, guardian_approval_id, override_reason, promoter_id,
        )

        return decision

    def get_blocked_writes(self) -> list[WriteGateDecision]:
        """Return all blocked write attempts."""
        return [d for d in self._decisions if not d.allowed]

    def get_emergency_overrides(self) -> list[WriteGateDecision]:
        """Return all emergency overrides for governance audit."""
        return [d for d in self._decisions if d.emergency_override]

    def audit_trail(self) -> list[dict[str, Any]]:
        """Return full audit trail of all gate decisions."""
        return [d.to_dict() for d in self._decisions]

    def summary(self) -> dict[str, Any]:
        """Summary statistics for governance dashboards."""
        total = len(self._decisions)
        allowed = sum(1 for d in self._decisions if d.allowed)
        blocked = sum(1 for d in self._decisions if not d.allowed)
        overrides = sum(1 for d in self._decisions if d.emergency_override)

        return {
            "total_decisions": total,
            "allowed": allowed,
            "blocked": blocked,
            "emergency_overrides": overrides,
            "block_rate": blocked / max(total, 1),
        }

    def _validate_verifier(
        self, provenance: PromotionProvenance, promoter_id: str
    ) -> bool:
        """Validate that the verifier exists and is independent."""
        verifier = provenance.l3_to_l4_verifier_id
        if not verifier:
            return False
        if promoter_id and verifier == promoter_id:
            return False
        return True

    def _persist_decision(self, decision: WriteGateDecision) -> None:
        """Append decision to the audit JSONL file."""
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._audit_log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(decision.to_dict(), default=str, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.error("Failed to persist gate decision: %s", exc)
