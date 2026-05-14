"""
Token Economy — System-wide token budgeting with priority tiers.

Works alongside the existing ContextBudgetManager but adds economy-level
tracking with priority-tiered allocation:

  CRITICAL   — Guaranteed allocation, never preempted
  STANDARD   — Best-effort allocation from available pool
  OPTIONAL   — Allocated only from surplus after CRITICAL and STANDARD

The TokenEconomy tracks utilization across agents and can propose
rebalancing based on historical usage patterns.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)


class BudgetTier(IntEnum):
    """Priority tier for token allocation."""
    CRITICAL = 1
    STANDARD = 2
    OPTIONAL = 3


@dataclass
class AgentAllocation:
    """Token allocation for a single agent."""
    agent_id: str
    tokens: int
    tier: BudgetTier
    used: int = 0
    allocated_at: float = field(default_factory=time.time)

    @property
    def remaining(self) -> int:
        return max(0, self.tokens - self.used)

    @property
    def utilization(self) -> float:
        return self.used / self.tokens if self.tokens > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tokens": self.tokens,
            "tier": self.tier.name,
            "used": self.used,
            "remaining": self.remaining,
            "utilization": round(self.utilization, 3),
            "allocated_at": datetime.fromtimestamp(
                self.allocated_at, tz=timezone.utc
            ).isoformat(),
        }


@dataclass
class RebalanceProposal:
    """A proposal for rebalancing token allocations across agents."""
    current_allocations: dict[str, int]
    proposed_allocations: dict[str, int]
    rationale: list[str]
    estimated_efficiency_gain: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_allocations": self.current_allocations,
            "proposed_allocations": self.proposed_allocations,
            "rationale": self.rationale,
            "estimated_efficiency_gain": round(self.estimated_efficiency_gain, 4),
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class TokenEconomy:
    """
    Manages a system-wide token economy with priority-tiered allocation.

    Usage:
        economy = TokenEconomy()
        economy.set_system_budget(200_000)
        economy.allocate_budget("agent-1", 50_000, BudgetTier.CRITICAL)
        economy.allocate_budget("agent-2", 30_000, BudgetTier.STANDARD)

        util = economy.get_utilization()
        proposal = economy.rebalance()
    """

    def __init__(self, system_budget: int = 0):
        self._system_budget = system_budget
        self._allocations: dict[str, AgentAllocation] = {}
        self._usage_history: list[dict[str, Any]] = []
        self._max_history = 500

    def set_system_budget(self, total_tokens: int) -> None:
        """Set the global token budget for the entire system."""
        self._system_budget = total_tokens
        logger.info("System token budget set to %d", total_tokens)

    @property
    def system_budget(self) -> int:
        return self._system_budget

    def allocate_budget(
        self,
        agent_id: str,
        tokens: int,
        tier: BudgetTier = BudgetTier.STANDARD,
    ) -> AgentAllocation | None:
        """
        Allocate tokens from the system pool to an agent.

        Returns the allocation if successful, None if insufficient budget.
        CRITICAL allocations are always honored if system budget allows.
        OPTIONAL allocations only succeed if surplus exists.
        """
        available = self._available_tokens()

        if tier == BudgetTier.OPTIONAL:
            surplus = self._surplus_tokens()
            if tokens > surplus:
                logger.warning(
                    "OPTIONAL allocation for %s rejected: requested %d, surplus %d",
                    agent_id, tokens, surplus,
                )
                return None

        if tokens > available:
            logger.warning(
                "Allocation for %s rejected: requested %d, available %d",
                agent_id, tokens, available,
            )
            return None

        allocation = AgentAllocation(
            agent_id=agent_id,
            tokens=tokens,
            tier=tier,
        )
        self._allocations[agent_id] = allocation

        self._usage_history.append({
            "event": "allocate",
            "agent_id": agent_id,
            "tokens": tokens,
            "tier": tier.name,
            "timestamp": time.time(),
        })
        if len(self._usage_history) > self._max_history:
            self._usage_history = self._usage_history[-self._max_history:]

        logger.info(
            "Allocated %d tokens to %s (tier=%s)", tokens, agent_id, tier.name,
        )
        return allocation

    def get_allocation(self, agent_id: str) -> AgentAllocation | None:
        """Get the current allocation for an agent."""
        return self._allocations.get(agent_id)

    def record_usage(self, agent_id: str, tokens: int) -> bool:
        """Record token usage against an agent's allocation."""
        alloc = self._allocations.get(agent_id)
        if not alloc:
            logger.warning("No allocation found for agent %s", agent_id)
            return False

        alloc.used += tokens
        return True

    def get_utilization(self) -> dict[str, Any]:
        """Get system-wide utilization metrics."""
        total_allocated = sum(a.tokens for a in self._allocations.values())
        total_used = sum(a.used for a in self._allocations.values())

        by_tier: dict[str, dict[str, int]] = {}
        for tier in BudgetTier:
            tier_allocs = [a for a in self._allocations.values() if a.tier == tier]
            by_tier[tier.name] = {
                "allocated": sum(a.tokens for a in tier_allocs),
                "used": sum(a.used for a in tier_allocs),
                "agents": len(tier_allocs),
            }

        return {
            "system_budget": self._system_budget,
            "total_allocated": total_allocated,
            "total_used": total_used,
            "total_remaining": self._system_budget - total_allocated,
            "allocation_ratio": round(
                total_allocated / self._system_budget, 3
            ) if self._system_budget > 0 else 0.0,
            "usage_ratio": round(
                total_used / total_allocated, 3
            ) if total_allocated > 0 else 0.0,
            "by_tier": by_tier,
            "agent_count": len(self._allocations),
        }

    def rebalance(self) -> RebalanceProposal:
        """
        Propose budget rebalancing based on usage patterns.

        Does NOT auto-apply — returns a proposal for review.
        """
        current = {a.agent_id: a.tokens for a in self._allocations.values()}
        proposed = dict(current)
        rationale: list[str] = []
        total_gain = 0.0

        over_allocated: list[AgentAllocation] = []
        under_allocated: list[AgentAllocation] = []

        for alloc in self._allocations.values():
            if alloc.utilization < 0.3 and alloc.tokens > 0:
                over_allocated.append(alloc)
            elif alloc.utilization > 0.85:
                under_allocated.append(alloc)

        reclaimable = 0
        for alloc in over_allocated:
            reduction = int(alloc.tokens * 0.3)
            proposed[alloc.agent_id] = alloc.tokens - reduction
            reclaimable += reduction
            rationale.append(
                f"Reduce {alloc.agent_id}: {alloc.utilization:.0%} utilization, "
                f"reclaim {reduction} tokens"
            )

        if reclaimable > 0 and under_allocated:
            share = reclaimable // len(under_allocated)
            for alloc in under_allocated:
                proposed[alloc.agent_id] = alloc.tokens + share
                rationale.append(
                    f"Increase {alloc.agent_id}: {alloc.utilization:.0%} utilization, "
                    f"add {share} tokens"
                )

        if reclaimable > 0:
            total_tokens = sum(current.values()) or 1
            total_gain = reclaimable / total_tokens * 0.5

        if not rationale:
            rationale.append("No rebalancing needed — allocations are well-utilized")

        return RebalanceProposal(
            current_allocations=current,
            proposed_allocations=proposed,
            rationale=rationale,
            estimated_efficiency_gain=total_gain,
        )

    def _available_tokens(self) -> int:
        """Tokens not yet allocated to any agent."""
        allocated = sum(a.tokens for a in self._allocations.values())
        return max(0, self._system_budget - allocated)

    def _surplus_tokens(self) -> int:
        """
        Tokens beyond what CRITICAL and STANDARD tiers need.

        OPTIONAL allocations draw from this pool.
        """
        committed = sum(
            a.tokens for a in self._allocations.values()
            if a.tier in (BudgetTier.CRITICAL, BudgetTier.STANDARD)
        )
        return max(0, self._system_budget - committed)
