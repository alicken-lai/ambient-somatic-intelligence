"""Promotion Chain Validator — ensures no level is skipped in the promotion hierarchy.

Core enforcement logic for the L1→L2→L3→L4 sequential promotion chain.
Every promotion must pass through this validator before execution.

Design principles:
  - Only adjacent-level transitions are valid (L1→L2, L2→L3, L3→L4)
  - Each transition has minimum confidence, recurrence, and verifier requirements
  - Active contradictions block promotion
  - All validation results include detailed pass/fail reasons for audit
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .layer_definition import MemoryLayer
from .promotion_rules import PROMOTION_RULES, PromotionRule

logger = logging.getLogger(__name__)


VALID_TRANSITIONS: dict[MemoryLayer, list[MemoryLayer]] = {
    MemoryLayer.L1_EPISODIC: [MemoryLayer.L2_INSTINCT],
    MemoryLayer.L2_INSTINCT: [MemoryLayer.L3_SKILL],
    MemoryLayer.L3_SKILL: [MemoryLayer.L4_STRATEGIC],
}

TRANSITION_REQUIREMENTS: dict[tuple[MemoryLayer, MemoryLayer], dict[str, Any]] = {
    (MemoryLayer.L1_EPISODIC, MemoryLayer.L2_INSTINCT): {
        "min_confidence": 0.7,
        "min_recurrence": 3,
        "requires_verifier": False,
        "requires_governance": False,
    },
    (MemoryLayer.L2_INSTINCT, MemoryLayer.L3_SKILL): {
        "min_confidence": 0.8,
        "min_recurrence": 5,
        "requires_verifier": False,
        "requires_governance": True,
    },
    (MemoryLayer.L3_SKILL, MemoryLayer.L4_STRATEGIC): {
        "min_confidence": 0.9,
        "min_recurrence": 10,
        "requires_verifier": True,
        "requires_governance": True,
    },
}


@dataclass
class ValidationResult:
    """Result of a promotion chain validation check."""

    valid: bool
    source_level: MemoryLayer
    target_level: MemoryLayer
    checks_passed: list[str]
    checks_failed: list[str]
    entry_id: str = ""
    confidence: float = 0.0
    recurrence: int = 0
    verifier_id: str = ""
    promoter_id: str = ""
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "entry_id": self.entry_id,
            "source_level": self.source_level.name,
            "target_level": self.target_level.name,
            "confidence": self.confidence,
            "recurrence": self.recurrence,
            "verifier_id": self.verifier_id,
            "promoter_id": self.promoter_id,
            "checks_passed": list(self.checks_passed),
            "checks_failed": list(self.checks_failed),
            "validated_at": self.validated_at.isoformat(),
        }

    @property
    def blocking_reasons(self) -> list[str]:
        """Alias for checks_failed, for compatibility with existing code."""
        return self.checks_failed


class PromotionChainValidator:
    """Validates that every promotion follows the sequential L1→L2→L3→L4 chain.

    Ensures:
      - Only adjacent-level transitions are allowed
      - Minimum confidence threshold is met for the transition
      - Minimum recurrence count is met
      - Verifier approval exists for L3→L4 (verifier != promoter)
      - No active contradictions block the promotion
    """

    def __init__(self) -> None:
        self._valid_transitions = VALID_TRANSITIONS
        self._requirements = TRANSITION_REQUIREMENTS

    def validate(
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
        """Validate a proposed promotion against all chain rules.

        Args:
            source_level: Current layer of the entry.
            target_level: Proposed target layer.
            confidence: Current confidence score of the entry.
            recurrence: Number of times the pattern has been observed.
            verifier_id: ID of the independent verifier (for L3→L4).
            promoter_id: ID of the entity proposing the promotion.
            contradiction_count: Number of active contradictions.
            entry_id: ID of the entry being promoted.

        Returns:
            ValidationResult with pass/fail status and detailed reasons.
        """
        passed: list[str] = []
        failed: list[str] = []

        # Check 1: Valid transition (no level skipping)
        valid_targets = self._valid_transitions.get(source_level, [])
        if target_level in valid_targets:
            passed.append(
                f"transition_valid: {source_level.name} → {target_level.name} is a valid adjacent transition"
            )
        else:
            failed.append(
                f"transition_invalid: {source_level.name} → {target_level.name} is NOT a valid transition. "
                f"Valid targets from {source_level.name}: {[t.name for t in valid_targets]}"
            )

        # Check 2: Minimum confidence threshold
        requirements = self._requirements.get((source_level, target_level))
        if requirements:
            min_conf = requirements["min_confidence"]
            if confidence >= min_conf:
                passed.append(
                    f"confidence_met: {confidence:.3f} >= {min_conf:.3f}"
                )
            else:
                failed.append(
                    f"confidence_insufficient: {confidence:.3f} < required {min_conf:.3f}"
                )

            # Check 3: Minimum recurrence count
            min_rec = requirements["min_recurrence"]
            if recurrence >= min_rec:
                passed.append(
                    f"recurrence_met: {recurrence} >= {min_rec}"
                )
            else:
                failed.append(
                    f"recurrence_insufficient: {recurrence} < required {min_rec}"
                )

            # Check 4: Verifier approval (L3→L4 only)
            if requirements["requires_verifier"]:
                if verifier_id:
                    if verifier_id != promoter_id:
                        passed.append(
                            f"verifier_independent: verifier={verifier_id!r} != promoter={promoter_id!r}"
                        )
                    else:
                        failed.append(
                            f"self_certification: verifier_id ({verifier_id!r}) == promoter_id — "
                            "independent verification required"
                        )
                else:
                    failed.append(
                        "verifier_missing: L3→L4 promotion requires verifier_id"
                    )
        else:
            if target_level not in valid_targets:
                failed.append(
                    f"no_requirements_defined: transition {source_level.name} → {target_level.name} "
                    "has no defined requirements (likely invalid)"
                )

        # Check 5: No active contradictions
        if contradiction_count > 0:
            failed.append(
                f"active_contradictions: {contradiction_count} contradiction(s) exist — "
                "resolve before promotion"
            )
        else:
            passed.append("no_contradictions: entry has no active contradictions")

        is_valid = len(failed) == 0

        result = ValidationResult(
            valid=is_valid,
            source_level=source_level,
            target_level=target_level,
            checks_passed=passed,
            checks_failed=failed,
            entry_id=entry_id,
            confidence=confidence,
            recurrence=recurrence,
            verifier_id=verifier_id,
            promoter_id=promoter_id,
        )

        if not is_valid:
            logger.warning(
                "Chain validation FAILED for %s: %s → %s — %s",
                entry_id or "(unknown)",
                source_level.name,
                target_level.name,
                "; ".join(failed),
            )

        return result

    def is_valid_transition(
        self, source_level: MemoryLayer, target_level: MemoryLayer
    ) -> bool:
        """Quick check if a transition is structurally valid (no level skip)."""
        valid_targets = self._valid_transitions.get(source_level, [])
        return target_level in valid_targets

    def get_next_valid_target(self, source_level: MemoryLayer) -> MemoryLayer | None:
        """Return the only valid next layer for a given source layer."""
        targets = self._valid_transitions.get(source_level, [])
        return targets[0] if targets else None

    def get_requirements(
        self, source_level: MemoryLayer, target_level: MemoryLayer
    ) -> dict[str, Any] | None:
        """Return the requirements dict for a specific transition."""
        return self._requirements.get((source_level, target_level))
