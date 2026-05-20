"""Attention stabilizer — advisory focus redistribution hints."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class AttentionStabilizer:
    """Recommends stabilization when attention pathology or entropy is elevated."""

    ENTROPY_THRESHOLD = 0.72
    OVERRUN_THRESHOLD = 0.35

    def pressure(
        self,
        *,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        pathology_pressure: float = 0.0,
    ) -> float:
        p = clamp01(focus_entropy * 0.5 + pathology_pressure * 0.35)
        if budget_overrun:
            p = clamp01(p + 0.25)
        return p

    def recommend(
        self,
        *,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        pathology_pressure: float = 0.0,
    ) -> list[str]:
        recs: list[str] = []
        if focus_entropy >= self.ENTROPY_THRESHOLD:
            recs.append("reduce_focus_entropy_via_competition_rebalance")
        if budget_overrun:
            recs.append("defer_non_critical_submissions_until_budget_recovered")
        if pathology_pressure >= self.OVERRUN_THRESHOLD:
            recs.append("apply_attention_pathology_containment_window")
        return recs

    def assess(
        self,
        *,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        pathology_pressure: float = 0.0,
    ) -> dict[str, Any]:
        p = self.pressure(
            focus_entropy=focus_entropy,
            budget_overrun=budget_overrun,
            pathology_pressure=pathology_pressure,
        )
        return {
            "pressure": round(p, 4),
            "recommendations": self.recommend(
                focus_entropy=focus_entropy,
                budget_overrun=budget_overrun,
                pathology_pressure=pathology_pressure,
            ),
            "disclaimer": "advisory_only_no_kernel_override",
        }
