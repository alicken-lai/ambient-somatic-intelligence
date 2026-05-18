"""Promotion Guard — top-level wrapper that intercepts all promotion operations.

Sits between callers and the PromotionEngine to enforce chain validation.
All promotion attempts (approved AND blocked) are logged for full audit trail.

Design:
  - Composable: wraps existing PromotionEngine without replacing it
  - Non-invasive: existing valid L1→L2 promotions continue to work
  - Comprehensive logging: every attempt is recorded regardless of outcome
  - Backward compatible: the guard_promotion API returns the same PromotionResult
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer
from .promotion_chain_validator import PromotionChainValidator, ValidationResult
from .promotion_engine import PromotionCandidate, PromotionEngine, PromotionResult
from .promotion_violation import PromotionViolation, ViolationLog

logger = logging.getLogger(__name__)


@dataclass
class GuardedPromotionResult:
    """Extended promotion result with chain validation details."""

    promotion_result: PromotionResult
    chain_validation: ValidationResult
    violation: PromotionViolation | None
    guard_action: str  # "approved", "blocked_chain", "blocked_ineligible"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "guard_action": self.guard_action,
            "promotion_result": self.promotion_result.to_dict(),
            "chain_validation": self.chain_validation.to_dict(),
        }
        if self.violation:
            result["violation"] = self.violation.to_dict()
        return result

    @property
    def approved(self) -> bool:
        """Whether the promotion was ultimately approved."""
        return self.promotion_result.approved


class PromotionGuard:
    """Top-level promotion guard that wraps all promotion operations.

    Intercepts every promotion request, validates the chain is not skipped,
    and logs all attempts (approved and blocked).

    Usage:
        engine = PromotionEngine(rules, confidence_model)
        guard = PromotionGuard(engine)

        result = guard.guard_promotion(
            candidate=candidate,
            governance_decision_id="GOV-123",
            verifier_id="verifier-agent-1",
            promoter_id="skillify-agent",
            recurrence=12,
            contradiction_count=0,
        )

        if result.approved:
            # promotion was valid and executed
            ...
        else:
            # promotion was blocked — check result.chain_validation
            ...
    """

    def __init__(
        self,
        engine: PromotionEngine,
        chain_validator: PromotionChainValidator | None = None,
        violation_log: ViolationLog | None = None,
    ) -> None:
        self._engine = engine
        self._chain_validator = chain_validator or PromotionChainValidator()
        self._violation_log = violation_log or ViolationLog()
        self._audit: list[dict[str, Any]] = []

    def guard_promotion(
        self,
        candidate: PromotionCandidate,
        governance_decision_id: str = "",
        verifier_id: str | None = None,
        promoter_id: str = "",
        recurrence: int = 0,
        contradiction_count: int = 0,
    ) -> GuardedPromotionResult:
        """Validate and execute a promotion with full chain enforcement.

        This is the primary API. It:
          1. Validates the chain (no level skipping)
          2. If valid, delegates to PromotionEngine.approve_promotion
          3. If invalid, blocks and logs a violation
          4. Returns a comprehensive result in all cases

        Args:
            candidate: The promotion candidate (must already be proposed).
            governance_decision_id: Governance approval ID.
            verifier_id: Independent verifier ID (required for L3→L4).
            promoter_id: ID of the entity requesting the promotion.
            recurrence: Number of observed occurrences of the pattern.
            contradiction_count: Active contradictions against this entry.

        Returns:
            GuardedPromotionResult with full audit context.
        """
        chain_result = self._chain_validator.validate(
            source_level=candidate.source_layer,
            target_level=candidate.target_layer,
            confidence=candidate.confidence,
            recurrence=recurrence,
            verifier_id=verifier_id or "",
            promoter_id=promoter_id,
            contradiction_count=contradiction_count,
            entry_id=candidate.entry_id,
        )

        self._log_attempt(candidate, chain_result, governance_decision_id)

        if not chain_result.valid:
            violation = self._violation_log.create_and_record(
                source_level=candidate.source_layer.name,
                target_level=candidate.target_layer.name,
                reason="; ".join(chain_result.checks_failed),
                confidence=candidate.confidence,
                recurrence=recurrence,
                governance_reference=governance_decision_id,
                blocked=True,
                source_file="promotion_guard",
                source_function="guard_promotion",
                entry_id=candidate.entry_id,
                additional_context={
                    "candidate_id": candidate.candidate_id,
                    "promoter_id": promoter_id,
                    "verifier_id": verifier_id or "",
                },
            )

            blocked_result = PromotionResult(
                candidate=candidate,
                approved=False,
                new_entry_id=None,
                governance_decision_id=governance_decision_id or None,
                verifier_id=verifier_id,
                reason=f"Chain validation failed: {'; '.join(chain_result.checks_failed)}",
            )

            return GuardedPromotionResult(
                promotion_result=blocked_result,
                chain_validation=chain_result,
                violation=violation,
                guard_action="blocked_chain",
            )

        promotion_result = self._engine.approve_promotion(
            candidate_id=candidate.candidate_id,
            governance_decision_id=governance_decision_id,
            verifier_id=verifier_id,
        )

        guard_action = "approved" if promotion_result.approved else "blocked_ineligible"

        if not promotion_result.approved:
            self._violation_log.create_and_record(
                source_level=candidate.source_layer.name,
                target_level=candidate.target_layer.name,
                reason=f"Engine rejection: {promotion_result.reason}",
                confidence=candidate.confidence,
                recurrence=recurrence,
                governance_reference=governance_decision_id,
                blocked=True,
                source_file="promotion_guard",
                source_function="guard_promotion (engine rejection)",
                entry_id=candidate.entry_id,
            )

        return GuardedPromotionResult(
            promotion_result=promotion_result,
            chain_validation=chain_result,
            violation=None,
            guard_action=guard_action,
        )

    def validate_only(
        self,
        source_level: MemoryLayer,
        target_level: MemoryLayer,
        confidence: float = 0.0,
        recurrence: int = 0,
        verifier_id: str = "",
        promoter_id: str = "",
        contradiction_count: int = 0,
        entry_id: str = "",
    ) -> ValidationResult:
        """Run chain validation without executing promotion.

        Useful for pre-flight checks before proposing a promotion.
        """
        return self._chain_validator.validate(
            source_level=source_level,
            target_level=target_level,
            confidence=confidence,
            recurrence=recurrence,
            verifier_id=verifier_id,
            promoter_id=promoter_id,
            contradiction_count=contradiction_count,
            entry_id=entry_id,
        )

    def get_violation_log(self) -> ViolationLog:
        """Access the violation log for governance queries."""
        return self._violation_log

    def audit_trail(self) -> list[dict[str, Any]]:
        """Return the guard's audit trail of all promotion attempts."""
        return list(self._audit)

    def _log_attempt(
        self,
        candidate: PromotionCandidate,
        chain_result: ValidationResult,
        governance_decision_id: str,
    ) -> None:
        """Log every promotion attempt for full audit."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_id": candidate.candidate_id,
            "entry_id": candidate.entry_id,
            "source_layer": candidate.source_layer.name,
            "target_layer": candidate.target_layer.name,
            "confidence": candidate.confidence,
            "chain_valid": chain_result.valid,
            "governance_decision_id": governance_decision_id,
            "checks_passed": chain_result.checks_passed,
            "checks_failed": chain_result.checks_failed,
        }
        self._audit.append(entry)
        logger.info(
            "Promotion attempt: %s → %s (entry=%s, chain_valid=%s)",
            candidate.source_layer.name,
            candidate.target_layer.name,
            candidate.entry_id,
            chain_result.valid,
        )
