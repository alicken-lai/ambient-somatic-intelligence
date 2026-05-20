"""Runtime attention metrics — kernel + adapter evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.kernel.attention_kernel import AttentionKernel
from observability.v05.attention_metrics import AttentionMetrics, collect_attention_metrics


@dataclass
class RuntimeAttentionMetrics(AttentionMetrics):
    submissions: int = 0
    explainability_coverage: float = 1.0
    adapter_ok: bool = True
    routes_active: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "submissions": self.submissions,
            "explainability_coverage": round(self.explainability_coverage, 4),
            "adapter_ok": self.adapter_ok,
            "routes_active": list(self.routes_active),
        })
        return base


def collect_runtime_attention_metrics(
    kernel: AttentionKernel,
    *,
    submissions: int = 0,
    explainability_coverage: float = 1.0,
) -> RuntimeAttentionMetrics:
    base = collect_attention_metrics(kernel.state, kernel.queue)
    return RuntimeAttentionMetrics(
        focused_count=base.focused_count,
        queue_depth=base.queue_depth,
        budget_remaining=base.budget_remaining,
        fatigue_level=base.fatigue_level,
        mean_salience=base.mean_salience,
        max_salience=base.max_salience,
        submissions=submissions,
        explainability_coverage=explainability_coverage,
        adapter_ok=True,
        routes_active=["R1", "R2", "R3"],
    )
