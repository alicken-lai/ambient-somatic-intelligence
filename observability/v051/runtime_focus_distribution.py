"""Focus slot distribution across domains."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.kernel.attention_kernel import AttentionKernel


@dataclass
class RuntimeFocusDistribution:
    by_domain: dict[str, int] = field(default_factory=dict)
    total_focused: int = 0
    entropy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "by_domain": dict(self.by_domain),
            "total_focused": self.total_focused,
            "entropy": round(self.entropy, 4),
        }


def compute_runtime_focus_distribution(kernel: AttentionKernel) -> RuntimeFocusDistribution:
    by_domain: dict[str, int] = {}
    for t in kernel.state.focused_targets:
        by_domain[t.source_domain] = by_domain.get(t.source_domain, 0) + 1
    total = sum(by_domain.values())
    if total == 0:
        return RuntimeFocusDistribution(by_domain=by_domain, total_focused=0, entropy=0.0)
    probs = [c / total for c in by_domain.values()]
    import math

    ent = -sum(p * math.log(p + 1e-12) for p in probs)
    return RuntimeFocusDistribution(by_domain=by_domain, total_focused=total, entropy=ent)
