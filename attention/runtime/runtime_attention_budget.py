"""
Runtime attention budget — finite per-cycle allocation of attention capacity.

Tracks a bounded budget that callers draw down via :meth:`try_allocate`.  When
insufficient budget remains the allocation is refused.  The budget is mirrored
onto :attr:`AttentionKernelState.budget_remaining` so observability can read it.
"""

from __future__ import annotations

from typing import Any

from attention.kernel.attention_kernel import AttentionKernel


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class RuntimeAttentionBudget:
    """Finite attention budget with per-domain accounting."""

    def __init__(self, kernel: AttentionKernel, total: float = 1.0) -> None:
        self.kernel = kernel
        self.total = max(0.0, float(total))
        self.remaining = self.total
        self.by_domain: dict[str, float] = {}
        self.kernel.state.budget_remaining = _clamp_unit(self.remaining / self.total) if self.total else 0.0

    def try_allocate(self, domain: str, amount: float) -> bool:
        amount = max(0.0, float(amount))
        if amount > self.remaining:
            return False
        self.remaining -= amount
        self.by_domain[domain] = self.by_domain.get(domain, 0.0) + amount
        if self.total:
            self.kernel.state.budget_remaining = _clamp_unit(self.remaining / self.total)
        return True

    def replenish(self, amount: float | None = None) -> None:
        if amount is None:
            self.remaining = self.total
        else:
            self.remaining = min(self.total, self.remaining + max(0.0, float(amount)))
        if self.total:
            self.kernel.state.budget_remaining = _clamp_unit(self.remaining / self.total)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 4),
            "remaining": round(self.remaining, 4),
            "by_domain": {k: round(v, 4) for k, v in self.by_domain.items()},
        }
