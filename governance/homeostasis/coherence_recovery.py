"""Coherence recovery — advisory steps when coherence pressure is elevated."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class CoherenceRecovery:
    RECOVERY_FLOOR = 0.55

    def gap(self, *, coherence_score: float, coherence_ok: bool) -> float:
        if coherence_ok and coherence_score >= self.RECOVERY_FLOOR:
            return 0.0
        return clamp01(self.RECOVERY_FLOOR - coherence_score)

    def pressure(
        self,
        *,
        coherence_score: float,
        coherence_ok: bool,
        coherence_verdict: dict[str, Any] | None = None,
    ) -> float:
        base = self.gap(coherence_score=coherence_score, coherence_ok=coherence_ok)
        if coherence_verdict:
            reasons = coherence_verdict.get("reasons") or []
            if reasons:
                base = clamp01(base + min(0.25, len(reasons) * 0.08))
        return base

    def recommend(
        self,
        *,
        coherence_score: float,
        coherence_ok: bool,
    ) -> list[str]:
        if coherence_ok and coherence_score >= self.RECOVERY_FLOOR:
            return []
        recs = ["pause_high_salience_submissions_pending_coherence_review"]
        if coherence_score < 0.4:
            recs.append("trigger_provenance_reconciliation_pass")
        return recs

    def assess(
        self,
        *,
        coherence_score: float,
        coherence_ok: bool,
        coherence_verdict: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "coherence_gap": round(
                self.gap(coherence_score=coherence_score, coherence_ok=coherence_ok), 4
            ),
            "pressure": round(
                self.pressure(
                    coherence_score=coherence_score,
                    coherence_ok=coherence_ok,
                    coherence_verdict=coherence_verdict,
                ),
                4,
            ),
            "recommendations": self.recommend(
                coherence_score=coherence_score, coherence_ok=coherence_ok
            ),
            "disclaimer": "recovery_advisory_no_governance_override",
        }
