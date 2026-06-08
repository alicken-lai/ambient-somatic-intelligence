"""
Runtime attention explainer — explains a live target against the kernel.

Wraps :func:`explain_attention` for use at runtime: it scores a target through
the kernel's salience engine (if it has no salience yet) and returns a compact,
non-opaque summary suitable for runtime observability.
"""

from __future__ import annotations

from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.explainability.explain_attention import explain_attention
from attention.kernel.attention_kernel import AttentionKernel


class RuntimeAttentionExplainer:
    """Produces runtime explanations for attention targets."""

    def __init__(self, kernel: AttentionKernel) -> None:
        self.kernel = kernel

    def explain_target(self, target: AttentionTarget) -> dict[str, Any]:
        salience = target.salience or self.kernel.engine.compute(target)
        explanation = explain_attention(salience)
        children = explanation.breakdown.children
        return {
            "target_id": target.target_id,
            "total": salience.total,
            "dominant_factor": explanation.dominant_factor,
            "summary": explanation.summary,
            "runtime_summary": {
                "opaque": False,
                "factor_count": sum(1 for c in children if c.contribution > 0.0),
                "dominant_factor": explanation.dominant_factor,
            },
        }
