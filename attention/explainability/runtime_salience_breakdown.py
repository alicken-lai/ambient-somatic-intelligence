"""
Runtime salience breakdown — compact per-factor summary of a salience vector.

Provides a lightweight summary (factor count, top factors) of a
:class:`SalienceVector` for runtime dashboards, building on
:func:`explain_attention`.
"""

from __future__ import annotations

from typing import Any

from attention.core.salience import SalienceVector
from attention.explainability.explain_attention import explain_attention


def runtime_breakdown_summary(salience: SalienceVector, top_n: int = 3) -> dict[str, Any]:
    """Summarise *salience* into a compact, non-opaque breakdown."""
    explanation = explain_attention(salience)
    contributing = [c for c in explanation.breakdown.children if c.contribution > 0.0]
    contributing.sort(key=lambda c: c.contribution, reverse=True)
    return {
        "total": round(salience.total, 4),
        "factor_count": len(contributing),
        "dominant_factor": explanation.dominant_factor,
        "top_factors": [
            {"name": c.name, "contribution": round(c.contribution, 4)}
            for c in contributing[: max(1, top_n)]
        ],
        "opaque": False,
    }
