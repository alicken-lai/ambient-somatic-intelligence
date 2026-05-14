"""
Context Firewall — Prevent cross-task context leakage and enforce budgets.

Filters context blocks by ownership and task scope, validates context injections
between agents, and enforces per-agent token budgets. Each check produces a
typed result with a reason for auditability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from runtime.isolation_kernel.boundary_definitions import IsolationPolicy

log = logging.getLogger(__name__)


@dataclass
class FilterResult:
    original_blocks: int
    filtered_blocks: int
    removed_blocks: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_blocks": self.original_blocks,
            "filtered_blocks": self.filtered_blocks,
            "removed_blocks": self.removed_blocks,
            "reason": self.reason,
        }


@dataclass
class InjectionCheckResult:
    allowed: bool
    source: str
    target_agent: str
    tokens: int
    budget_remaining: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "source": self.source,
            "target_agent": self.target_agent,
            "tokens": self.tokens,
            "budget_remaining": self.budget_remaining,
            "reason": self.reason,
        }


@dataclass
class BudgetCheckResult:
    within_budget: bool
    current_tokens: int
    max_tokens: int
    utilization: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "within_budget": self.within_budget,
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "utilization": round(self.utilization, 4),
        }


class ContextFirewall:
    """Enforces context isolation and token budgets per agent."""

    def __init__(self, policy: IsolationPolicy) -> None:
        self._policy = policy

    @property
    def policy(self) -> IsolationPolicy:
        return self._policy

    def filter_context(
        self,
        context_blocks: list[dict],
        task_id: str,
    ) -> FilterResult:
        kept: list[dict] = []
        removed: list[str] = []

        for block in context_blocks:
            block_task = block.get("task_id", task_id)
            block_agent = block.get("agent_id")

            if block_task != task_id and block_agent != self._policy.agent_id:
                block_label = block.get("id", block.get("type", "unknown"))
                removed.append(str(block_label))
                continue

            block_layer = block.get("layer")
            if block_layer and block_layer not in self._policy.readable_memory_layers:
                removed.append(
                    f"{block.get('id', 'unknown')}:layer={block_layer}"
                )
                continue

            kept.append(block)

        reason = "All blocks passed" if not removed else f"Removed {len(removed)} cross-boundary blocks"
        return FilterResult(
            original_blocks=len(context_blocks),
            filtered_blocks=len(kept),
            removed_blocks=removed,
            reason=reason,
        )

    def check_injection(
        self,
        source: str,
        target_agent: str,
        tokens: int,
    ) -> InjectionCheckResult:
        budget_remaining = self._policy.max_context_tokens - tokens

        if target_agent != self._policy.agent_id:
            return InjectionCheckResult(
                allowed=False,
                source=source,
                target_agent=target_agent,
                tokens=tokens,
                budget_remaining=max(0, budget_remaining),
                reason=(
                    f"Injection target '{target_agent}' does not match "
                    f"firewall agent '{self._policy.agent_id}'"
                ),
            )

        if tokens > self._policy.max_context_tokens:
            return InjectionCheckResult(
                allowed=False,
                source=source,
                target_agent=target_agent,
                tokens=tokens,
                budget_remaining=0,
                reason=(
                    f"Injection of {tokens} tokens exceeds budget "
                    f"of {self._policy.max_context_tokens}"
                ),
            )

        allowed_sources = {"orchestrator", "system", "self", self._policy.agent_id}
        allowed_sources.update(self._policy.communication_channels)

        if source not in allowed_sources:
            return InjectionCheckResult(
                allowed=False,
                source=source,
                target_agent=target_agent,
                tokens=tokens,
                budget_remaining=max(0, budget_remaining),
                reason=f"Source '{source}' is not an allowed injection source",
            )

        return InjectionCheckResult(
            allowed=True,
            source=source,
            target_agent=target_agent,
            tokens=tokens,
            budget_remaining=max(0, budget_remaining),
            reason="Injection permitted",
        )

    def enforce_token_budget(
        self,
        agent_id: str,
        current_tokens: int,
    ) -> BudgetCheckResult:
        max_tokens = self._policy.max_context_tokens
        utilization = current_tokens / max_tokens if max_tokens > 0 else 1.0
        within_budget = current_tokens <= max_tokens
        return BudgetCheckResult(
            within_budget=within_budget,
            current_tokens=current_tokens,
            max_tokens=max_tokens,
            utilization=utilization,
        )

    def isolate_task_context(self, task_id: str, context: dict) -> dict:
        isolated = {}
        for key, value in context.items():
            if key in ("cross_task_refs", "other_agent_state", "shared_memory"):
                log.debug(
                    "Stripped cross-boundary key '%s' from task %s context",
                    key, task_id,
                )
                continue
            if isinstance(value, dict):
                ref_task = value.get("task_id")
                ref_agent = value.get("agent_id")
                if ref_task and ref_task != task_id and ref_agent != self._policy.agent_id:
                    log.debug(
                        "Stripped cross-task reference '%s' (task=%s) from context",
                        key, ref_task,
                    )
                    continue
            isolated[key] = value
        return isolated
