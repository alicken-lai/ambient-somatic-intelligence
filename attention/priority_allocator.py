"""
Priority Allocator — Attention budget and capacity management.

Models attention as a **finite resource**: the system cannot attend to
everything simultaneously.  The allocator:

  1. Maintains an ``AttentionBudget`` (max concurrent signals, per-domain
     budget fractions, remaining capacity).
  2. Accepts scored candidates and decides which are allocated, deferred,
     or rejected.
  3. Supports governance-mandated "must-attend" signals that bypass budget
     constraints (BLOCK-level risk).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from attention.attention_state import AttentionSignal
from attention.salience_engine import SalienceScore

logger = logging.getLogger(__name__)


# Default per-domain budget fractions (must sum to ≤ 1.0).
_DEFAULT_DOMAIN_BUDGETS: dict[str, float] = {
    "somatic": 0.30,
    "governance": 0.25,
    "task": 0.20,
    "memory": 0.15,
    "external": 0.10,
}


@dataclass
class AttentionBudget:
    """
    Capacity model for the attention layer.

    Tracks how many signals can be attended concurrently and how much
    budget each domain has consumed.
    """
    max_concurrent_signals: int = 10
    allocated: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_DOMAIN_BUDGETS))
    _consumed: dict[str, float] = field(default_factory=dict)
    _signal_amounts: dict[str, float] = field(default_factory=dict)

    @property
    def available(self) -> float:
        """Remaining total capacity (1.0 = fully available)."""
        used = sum(self._consumed.values())
        return max(0.0, 1.0 - used)

    @property
    def active_count(self) -> int:
        """Number of signals currently holding budget."""
        return len(self._signal_amounts)

    def allocate(self, signal: AttentionSignal, amount: float) -> bool:
        """
        Try to allocate *amount* of budget for *signal*.

        Returns ``True`` if the allocation succeeded.
        """
        domain = signal.source_domain
        domain_cap = self.allocated.get(domain, 0.05)
        domain_used = self._consumed.get(domain, 0.0)

        if domain_used + amount > domain_cap:
            logger.debug(
                "Budget exhausted for domain '%s' (used=%.2f, cap=%.2f, requested=%.2f)",
                domain, domain_used, domain_cap, amount,
            )
            return False

        if self.active_count >= self.max_concurrent_signals:
            logger.debug(
                "Max concurrent signals reached (%d)", self.max_concurrent_signals,
            )
            return False

        self._consumed[domain] = domain_used + amount
        self._signal_amounts[signal.signal_id] = amount
        return True

    def release(self, signal_id: str) -> float:
        """
        Release the budget held by *signal_id*.

        Returns the amount freed (0.0 if the signal was not tracked).
        """
        amount = self._signal_amounts.pop(signal_id, 0.0)
        if amount > 0.0:
            for domain in list(self._consumed):
                if self._consumed[domain] >= amount:
                    self._consumed[domain] -= amount
                    if self._consumed[domain] < 1e-9:
                        del self._consumed[domain]
                    break
        return amount

    def rebalance(self) -> dict[str, float]:
        """
        Redistribute domain budgets proportionally to current demand.

        Returns the updated allocation map.
        """
        total_consumed = sum(self._consumed.values()) or 1.0
        for domain in self.allocated:
            demand = self._consumed.get(domain, 0.0) / total_consumed
            self.allocated[domain] = max(0.05, demand * 0.7 + self.allocated[domain] * 0.3)

        # Re-normalise so fractions sum to 1.0
        total = sum(self.allocated.values())
        if total > 0:
            self.allocated = {k: v / total for k, v in self.allocated.items()}

        logger.info("Budget rebalanced: %s", {k: round(v, 3) for k, v in self.allocated.items()})
        return dict(self.allocated)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_concurrent_signals": self.max_concurrent_signals,
            "allocated": {k: round(v, 4) for k, v in self.allocated.items()},
            "consumed": {k: round(v, 4) for k, v in self._consumed.items()},
            "available": round(self.available, 4),
            "active_count": self.active_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttentionBudget:
        budget = cls(
            max_concurrent_signals=data.get("max_concurrent_signals", 10),
            allocated=data.get("allocated", dict(_DEFAULT_DOMAIN_BUDGETS)),
        )
        budget._consumed = data.get("consumed", {})
        return budget


# ------------------------------------------------------------------
# Allocation result
# ------------------------------------------------------------------

@dataclass
class AllocationEntry:
    """A single allocation decision for one signal."""
    signal_id: str
    budget_amount: float

    def to_dict(self) -> dict[str, Any]:
        return {"signal_id": self.signal_id, "budget_amount": round(self.budget_amount, 4)}


@dataclass
class AllocationResult:
    """Outcome of a priority allocation round."""
    allocated: list[AllocationEntry] = field(default_factory=list)
    deferred: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allocated": [a.to_dict() for a in self.allocated],
            "deferred": self.deferred,
            "rejected": self.rejected,
            "reasoning": self.reasoning,
        }


# ------------------------------------------------------------------
# Priority Allocator
# ------------------------------------------------------------------

class PriorityAllocator:
    """
    Allocates finite attention budget to scored signal candidates.

    Usage::

        allocator = PriorityAllocator()
        result = allocator.allocate(candidates, budget)
        for entry in result.allocated:
            print(entry.signal_id, entry.budget_amount)
    """

    MUST_ATTEND_SALIENCE = 0.85
    MIN_ALLOCATION = 0.02

    def __init__(
        self,
        governance_override_threshold: float = 0.9,
    ) -> None:
        self._governance_threshold = governance_override_threshold

    def allocate(
        self,
        candidates: list[tuple[AttentionSignal, SalienceScore]],
        budget: AttentionBudget,
    ) -> AllocationResult:
        """
        Allocate budget to candidates ordered by salience score.

        Governance BLOCK-level signals bypass budget constraints.
        """
        must_attend: list[tuple[AttentionSignal, SalienceScore]] = []
        normal: list[tuple[AttentionSignal, SalienceScore]] = []

        for signal, score in candidates:
            if self._is_must_attend(signal, score):
                must_attend.append((signal, score))
            else:
                normal.append((signal, score))

        normal.sort(key=lambda pair: pair[1].total, reverse=True)

        allocated: list[AllocationEntry] = []
        deferred: list[str] = []
        rejected: list[str] = []

        for signal, score in must_attend:
            amount = max(self.MIN_ALLOCATION, score.total * 0.15)
            budget.allocate(signal, amount)
            allocated.append(AllocationEntry(signal.signal_id, amount))
            logger.info(
                "Must-attend allocation: %s (salience=%.3f)",
                signal.signal_id[:8], score.total,
            )

        for signal, score in normal:
            if score.total < 0.1:
                rejected.append(signal.signal_id)
                continue

            amount = max(self.MIN_ALLOCATION, score.total * 0.10)
            if budget.allocate(signal, amount):
                allocated.append(AllocationEntry(signal.signal_id, amount))
            else:
                deferred.append(signal.signal_id)

        reasoning = (
            f"Allocated {len(allocated)} signals "
            f"(must-attend={len(must_attend)}), "
            f"deferred {len(deferred)}, rejected {len(rejected)}. "
            f"Budget remaining: {budget.available:.2%}"
        )

        result = AllocationResult(
            allocated=allocated,
            deferred=deferred,
            rejected=rejected,
            reasoning=reasoning,
        )

        logger.info("Allocation complete: %s", reasoning)
        return result

    def _is_must_attend(
        self,
        signal: AttentionSignal,
        score: SalienceScore,
    ) -> bool:
        """Check if a signal must bypass budget constraints."""
        if signal.metadata.get("governance_risk_level") == "BLOCK":
            return True
        if signal.metadata.get("must_attend", False):
            return True
        if (
            signal.source_domain == "governance"
            and score.total >= self._governance_threshold
        ):
            return True
        return score.total >= self.MUST_ATTEND_SALIENCE
