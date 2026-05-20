"""Cognition quality — bounded quality score from governance outcomes."""

from __future__ import annotations

from typing import Any

from observability.v04.metric_normalizer import clamp01


class CognitionQuality:
    QUALITY_FLOOR = 0.50

    def score(
        self,
        *,
        governed_salience: float,
        coherence_score: float,
        constitutional_compliant: bool = True,
        identity_trusted: bool = True,
        accepted: bool = True,
    ) -> float:
        base = clamp01(
            governed_salience * 0.35
            + coherence_score * 0.45
            + (0.2 if constitutional_compliant else 0.0)
        )
        if not identity_trusted:
            base = clamp01(base * 0.88)
        if not accepted:
            base = clamp01(base * 0.75)
        return base

    def assess(
        self,
        *,
        governed_salience: float,
        coherence_score: float,
        constitutional_compliant: bool = True,
        identity_trusted: bool = True,
        accepted: bool = True,
    ) -> dict[str, Any]:
        s = self.score(
            governed_salience=governed_salience,
            coherence_score=coherence_score,
            constitutional_compliant=constitutional_compliant,
            identity_trusted=identity_trusted,
            accepted=accepted,
        )
        return {
            "quality_score": round(s, 4),
            "acceptable": s >= self.QUALITY_FLOOR,
            "disclaimer": "quality_advisory_not_consciousness_claim",
        }
