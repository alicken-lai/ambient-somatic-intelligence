"""
Stabilization explainer — narrates a HomeostasisVerdict's stabilization state.

Identifies which bounded homeostatic pressure dominates and what advisory
recommendations follow. Read-only; carries no execution authority.
"""

from __future__ import annotations

from typing import Any

_PRESSURE_FIELDS = (
    "attention_pressure",
    "salience_variance",
    "coherence_gap",
    "reflection_load",
    "calibration_gap",
    "uncertainty_skew",
)


class StabilizationExplainer:
    """Explains a homeostasis verdict's dominant pressure and recommendations."""

    def explain_verdict(self, verdict: Any) -> dict[str, Any]:
        state = getattr(verdict, "stabilization_state", None) or {}
        pressures = {
            field: float(state.get(field, 0.0))
            for field in _PRESSURE_FIELDS
            if isinstance(state, dict)
        }
        dominant_pressure = "none"
        if pressures and max(pressures.values()) > 0.0:
            dominant_pressure = max(pressures, key=pressures.get)

        stable = bool(getattr(verdict, "stable", True))
        score = float(getattr(verdict, "homeostasis_score", 1.0))
        composite = float(getattr(verdict, "stabilization_pressure", 0.0))
        recommendations = [str(r) for r in getattr(verdict, "recommendations", []) or []]

        summary = (
            f"Homeostasis {'stable' if stable else 'stabilizing'} "
            f"(score={score:.4f}, pressure={composite:.4f}); "
            f"dominant pressure={dominant_pressure}."
        )

        return {
            "advisory_only": True,
            "stable": stable,
            "homeostasis_score": round(score, 4),
            "stabilization_pressure": round(composite, 4),
            "pressures": {k: round(v, 4) for k, v in pressures.items()},
            "dominant_pressure": dominant_pressure,
            "recommendations": recommendations,
            "summary": summary,
        }
