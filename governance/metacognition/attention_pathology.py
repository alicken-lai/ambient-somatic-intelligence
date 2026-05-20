"""Attention pathology — fixation, oscillation, and budget overrun signals."""

from __future__ import annotations

from observability.v04.metric_normalizer import clamp01


class AttentionPathology:
    def pressure(
        self,
        *,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        opaque_salience_count: int = 0,
        submission_count: int = 0,
    ) -> float:
        fixation = 0.25 if focus_entropy < 0.15 and submission_count > 5 else 0.0
        oscillation = 0.2 if focus_entropy > 0.92 and submission_count > 10 else 0.0
        overrun = 0.35 if budget_overrun else 0.0
        opaque = clamp01(opaque_salience_count * 0.08)
        return clamp01(fixation + oscillation + overrun + opaque)

    def labels(
        self,
        *,
        focus_entropy: float = 0.5,
        budget_overrun: bool = False,
        opaque_salience_count: int = 0,
        submission_count: int = 0,
    ) -> list[str]:
        labels: list[str] = []
        if focus_entropy < 0.15 and submission_count > 5:
            labels.append("attention_fixation")
        if focus_entropy > 0.92 and submission_count > 10:
            labels.append("attention_oscillation")
        if budget_overrun:
            labels.append("budget_overrun")
        if opaque_salience_count > 2:
            labels.append("opaque_salience_cluster")
        return labels
