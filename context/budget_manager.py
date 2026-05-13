"""
Context Budget Manager — Token budget allocation and enforcement.

Manages the scarce resource of context window tokens by:
  - Defining budget pools for different context types
  - Tracking consumption in real-time
  - Enforcing hard limits to prevent context overflow
  - Providing budget recommendations based on task complexity

Budget pools:
  system    — system prompts, rules, identity (fixed overhead)
  memory    — recalled memories, relevant history
  task      — current task description, user instructions
  code      — code snippets, file contents
  tools     — tool results, API responses
  reserve   — emergency buffer for tool responses

Token estimation uses a fast heuristic (4 chars ≈ 1 token for English,
2 chars ≈ 1 token for CJK).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BudgetPool:
    """A named allocation within the total context budget."""
    name: str
    max_tokens: int
    used_tokens: int = 0
    priority: int = 1  # 1=highest, 5=lowest (for dynamic reallocation)

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)

    @property
    def utilization(self) -> float:
        return self.used_tokens / self.max_tokens if self.max_tokens > 0 else 0.0

    @property
    def is_exhausted(self) -> bool:
        return self.used_tokens >= self.max_tokens

    def consume(self, tokens: int) -> int:
        """Consume tokens from this pool. Returns actual tokens consumed."""
        available = min(tokens, self.remaining)
        self.used_tokens += available
        return available

    def release(self, tokens: int) -> None:
        """Release tokens back to pool."""
        self.used_tokens = max(0, self.used_tokens - tokens)


CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


def estimate_tokens(text: str) -> int:
    """
    Fast token estimation heuristic.
    English/code: ~4 chars per token
    CJK: ~2 chars per token (each character is roughly 1 token)
    """
    if not text:
        return 0
    cjk_chars = len(CJK_PATTERN.findall(text))
    non_cjk_chars = len(text) - cjk_chars
    return int(cjk_chars * 0.7 + non_cjk_chars / 4)


DEFAULT_TOTAL_BUDGET = 128_000  # Typical LLM context window

DEFAULT_ALLOCATIONS = {
    "system": {"ratio": 0.05, "priority": 1},
    "memory": {"ratio": 0.25, "priority": 2},
    "task": {"ratio": 0.15, "priority": 1},
    "code": {"ratio": 0.30, "priority": 3},
    "tools": {"ratio": 0.15, "priority": 4},
    "reserve": {"ratio": 0.10, "priority": 5},
}


class ContextBudgetManager:
    """
    Manages token budget allocation across context pools.

    Usage:
        budget = ContextBudgetManager(total_tokens=128000)
        budget.can_fit("memory", some_text)  # Check before adding
        budget.consume("memory", some_text)   # Track consumption
        budget.report()                       # Get utilization report
    """

    def __init__(
        self,
        total_tokens: int = DEFAULT_TOTAL_BUDGET,
        allocations: dict[str, dict] | None = None,
    ):
        self.total_tokens = total_tokens
        allocs = allocations or DEFAULT_ALLOCATIONS
        self.pools: dict[str, BudgetPool] = {}

        for name, config in allocs.items():
            max_tokens = int(total_tokens * config["ratio"])
            priority = config.get("priority", 3)
            self.pools[name] = BudgetPool(name=name, max_tokens=max_tokens, priority=priority)

    @property
    def total_used(self) -> int:
        return sum(p.used_tokens for p in self.pools.values())

    @property
    def total_remaining(self) -> int:
        return self.total_tokens - self.total_used

    @property
    def utilization(self) -> float:
        return self.total_used / self.total_tokens if self.total_tokens > 0 else 0.0

    def can_fit(self, pool_name: str, text: str) -> bool:
        """Check if text can fit within pool's remaining budget."""
        pool = self.pools.get(pool_name)
        if not pool:
            return False
        tokens_needed = estimate_tokens(text)
        return tokens_needed <= pool.remaining

    def consume(self, pool_name: str, text: str) -> dict[str, Any]:
        """
        Consume tokens from a pool.

        Returns consumption details including whether it was truncated.
        """
        pool = self.pools.get(pool_name)
        if not pool:
            return {"error": f"Unknown pool: {pool_name}", "consumed": 0}

        tokens_needed = estimate_tokens(text)
        tokens_consumed = pool.consume(tokens_needed)
        truncated = tokens_consumed < tokens_needed

        return {
            "pool": pool_name,
            "tokens_needed": tokens_needed,
            "tokens_consumed": tokens_consumed,
            "truncated": truncated,
            "pool_remaining": pool.remaining,
            "pool_utilization": round(pool.utilization, 3),
        }

    def allocate_text(self, pool_name: str, text: str, max_chars: int | None = None) -> str:
        """
        Allocate text within budget, truncating if necessary.

        Returns the text (possibly truncated) that fits within budget.
        """
        pool = self.pools.get(pool_name)
        if not pool:
            return ""

        tokens_available = pool.remaining
        if tokens_available <= 0:
            return ""

        chars_budget = int(tokens_available * 3.5)
        if max_chars:
            chars_budget = min(chars_budget, max_chars)

        result = text[:chars_budget]
        self.consume(pool_name, result)
        return result

    def reallocate(self, from_pool: str, to_pool: str, tokens: int) -> bool:
        """Move budget from one pool to another (for dynamic adjustment)."""
        source = self.pools.get(from_pool)
        target = self.pools.get(to_pool)
        if not source or not target:
            return False

        available = source.remaining
        transfer = min(tokens, available)
        if transfer <= 0:
            return False

        source.max_tokens -= transfer
        target.max_tokens += transfer
        return True

    def suggest_allocation(self, task_type: str) -> dict[str, float]:
        """Suggest budget ratios based on task type."""
        presets = {
            "code_review": {"system": 0.05, "memory": 0.15, "task": 0.10, "code": 0.50, "tools": 0.10, "reserve": 0.10},
            "debugging": {"system": 0.05, "memory": 0.20, "task": 0.15, "code": 0.35, "tools": 0.15, "reserve": 0.10},
            "planning": {"system": 0.05, "memory": 0.35, "task": 0.25, "code": 0.10, "tools": 0.15, "reserve": 0.10},
            "memory_heavy": {"system": 0.05, "memory": 0.45, "task": 0.15, "code": 0.10, "tools": 0.15, "reserve": 0.10},
            "default": {"system": 0.05, "memory": 0.25, "task": 0.15, "code": 0.30, "tools": 0.15, "reserve": 0.10},
        }
        return presets.get(task_type, presets["default"])

    def apply_preset(self, task_type: str) -> None:
        """Apply a budget preset, redistributing allocations."""
        ratios = self.suggest_allocation(task_type)
        for name, ratio in ratios.items():
            if name in self.pools:
                pool = self.pools[name]
                pool.max_tokens = int(self.total_tokens * ratio)

    def report(self) -> dict[str, Any]:
        """Generate a budget utilization report."""
        pools_report = {}
        for name, pool in self.pools.items():
            pools_report[name] = {
                "max_tokens": pool.max_tokens,
                "used_tokens": pool.used_tokens,
                "remaining": pool.remaining,
                "utilization": round(pool.utilization, 3),
                "priority": pool.priority,
                "exhausted": pool.is_exhausted,
            }

        return {
            "total_tokens": self.total_tokens,
            "total_used": self.total_used,
            "total_remaining": self.total_remaining,
            "utilization": round(self.utilization, 3),
            "pools": pools_report,
            "warnings": self._generate_warnings(),
        }

    def _generate_warnings(self) -> list[str]:
        """Generate warnings about budget health."""
        warnings = []
        if self.utilization > 0.85:
            warnings.append(f"CRITICAL: Total context utilization at {self.utilization:.0%}")
        elif self.utilization > 0.70:
            warnings.append(f"WARNING: Total context utilization at {self.utilization:.0%}")

        for name, pool in self.pools.items():
            if pool.is_exhausted and pool.priority <= 3:
                warnings.append(f"Pool '{name}' exhausted (priority {pool.priority})")
            elif pool.utilization > 0.90 and pool.priority <= 2:
                warnings.append(f"Pool '{name}' near capacity ({pool.utilization:.0%})")

        return warnings


if __name__ == "__main__":
    import json

    budget = ContextBudgetManager(total_tokens=128_000)
    budget.consume("system", "You are Hermes, an ambient somatic intelligence runtime." * 10)
    budget.consume("memory", "Previous session: configured Cursor MCP connection." * 20)
    budget.consume("task", "Please refactor the memory architecture into layered stores.")
    print(json.dumps(budget.report(), indent=2))
