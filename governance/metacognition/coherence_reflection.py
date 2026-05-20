"""Coherence reflection — meta-view on post-governance coherence verdict."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class CoherenceReflection:
    def pressure(self, coherence_verdict: dict[str, Any] | None) -> float:
        if not coherence_verdict:
            return 0.15
        score = float(coherence_verdict.get("score", 1.0))
        reasons = coherence_verdict.get("reasons") or []
        base = clamp01(1.0 - score)
        reason_penalty = clamp01(len(reasons) * 0.12)
        return clamp01(base * 0.6 + reason_penalty)

    def reflect(self, coherence_verdict: dict[str, Any] | None) -> dict[str, Any]:
        p = self.pressure(coherence_verdict)
        coherent = bool(coherence_verdict.get("coherent", True)) if coherence_verdict else True
        return {
            "reflection_pressure": round(p, 4),
            "coherent_observed": coherent,
            "reasons_observed": list((coherence_verdict or {}).get("reasons") or []),
            "disclaimer": "coherence_reflection_advisory",
        }
