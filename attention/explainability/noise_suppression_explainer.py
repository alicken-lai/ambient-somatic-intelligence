"""
Noise suppression explainer — explains why a signal was (not) treated as noise.

Wraps :class:`NoiseClassifier` to provide a transparent rationale for each
suppression decision (e.g. "repetitive low salience" vs "above salience
ceiling").
"""

from __future__ import annotations

from typing import Any

from attention.consolidation.noise_classifier import NoiseClassifier


_REASON_TEXT: dict[str, str] = {
    "above_salience_ceiling": "kept: salience exceeds the noise ceiling",
    "repetitive_low_salience": "suppressed: repeats below the salience ceiling",
    "below_repeat_threshold": "kept: not yet repetitive enough to suppress",
}


class NoiseSuppressionExplainer:
    """Explains noise-suppression decisions for incoming signals."""

    def __init__(self, classifier: NoiseClassifier | None = None) -> None:
        self.classifier = classifier or NoiseClassifier()

    def explain(self, domain: str, signal_type: str, value: float) -> dict[str, Any]:
        classification = self.classifier.observe(domain, signal_type, value)
        return {
            "domain": domain,
            "signal_type": signal_type,
            "value": round(float(value), 4),
            "is_noise": classification.is_noise,
            "count": classification.count,
            "reason": classification.reason,
            "rationale": _REASON_TEXT.get(classification.reason, classification.reason),
            "opaque": False,
        }
