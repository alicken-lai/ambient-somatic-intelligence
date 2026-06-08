"""
Reflection breakdown — decomposes a MetacognitiveVerdict into its factors.

Shows which bounded pressures (degradation, pathology, coherence reflection,
calibration, boundary, introspection, recursion) shaped the reflection outcome.
Read-only and descriptive.
"""

from __future__ import annotations

from typing import Any

_FACTOR_FIELDS = (
    "degradation_pressure",
    "pathology_pressure",
    "coherence_reflection_pressure",
    "calibration_pressure",
    "boundary_pressure",
    "introspection_pressure",
    "recursive_pressure",
)


class ReflectionBreakdown:
    """Transparent decomposition of a metacognitive verdict."""

    def breakdown(self, verdict: Any) -> dict[str, Any]:
        factors = {
            field: round(float(getattr(verdict, field, 0.0)), 4)
            for field in _FACTOR_FIELDS
        }
        reflective = bool(getattr(verdict, "reflective", False))
        quality = float(getattr(verdict, "quality_score", 0.0))
        reasons = [str(r) for r in getattr(verdict, "reasons", []) or []]

        dominant = ""
        if factors:
            dominant = max(factors, key=factors.get)

        summary = (
            f"Reflection {'held' if reflective else 'damped'} "
            f"(quality_score={quality:.4f}); dominant factor={dominant}."
        )

        return {
            "advisory_only": True,
            "reflective": reflective,
            "quality_score": round(quality, 4),
            "factors": factors,
            "dominant_factor": dominant,
            "reasons": reasons,
            "summary": summary,
        }
