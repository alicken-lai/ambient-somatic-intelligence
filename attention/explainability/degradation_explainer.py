"""
Degradation explainer — explains declining cognition-quality pressure.

Wraps the governance degradation detector to report whether a series of quality
scores is trending downward and how much advisory degradation pressure results.
"""

from __future__ import annotations

from typing import Any

from governance.metacognition.degradation_detector import DegradationDetector


class DegradationExplainer:
    """Transparent breakdown of cognition-quality degradation over a series."""

    def explain_series(self, quality_series: list[float]) -> dict[str, Any]:
        detector = DegradationDetector()
        for q in quality_series:
            detector.record_quality(float(q))

        pressure = detector.pressure()
        is_degrading = detector.is_degrading()

        summary = (
            f"Over {len(quality_series)} quality sample(s), "
            f"degradation_pressure={pressure:.4f} (is_degrading={is_degrading}). "
            "Advisory trend signal, not a deterministic prognosis."
        )

        return {
            "advisory_only": True,
            "sample_count": len(quality_series),
            "degradation_pressure": round(pressure, 4),
            "is_degrading": is_degrading,
            "summary": summary,
        }
