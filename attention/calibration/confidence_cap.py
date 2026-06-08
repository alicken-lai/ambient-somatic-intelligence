"""
Confidence cap — the shared epistemic-humility primitive.

Reconstructed as a foundational primitive for the calibration layer.  The
single invariant is that calibrated confidence *never* reaches certainty:
``ABSOLUTE_MAX_CONFIDENCE`` is strictly below ``1.0``.  Both the somatic
calibration modules and the governance constitution depend on this ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass

ABSOLUTE_MAX_CONFIDENCE: float = 0.99


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


def apply_confidence_cap(value: float, cap: float = ABSOLUTE_MAX_CONFIDENCE) -> float:
    """Clamp *value* into ``[0.0, cap]`` with ``cap`` never above the absolute max."""
    ceiling = min(float(cap), ABSOLUTE_MAX_CONFIDENCE)
    return _clamp(value, 0.0, ceiling)


@dataclass
class CappedConfidence:
    """Outcome of capping a raw confidence value."""

    raw: float
    calibrated: float
    was_capped: bool

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "raw": round(self.raw, 6),
            "calibrated": round(self.calibrated, 6),
            "was_capped": self.was_capped,
        }


class ConfidenceCap:
    """Applies an absolute ceiling, optionally tightened per domain."""

    def __init__(
        self,
        absolute_max: float = ABSOLUTE_MAX_CONFIDENCE,
        domain_caps: dict[str, float] | None = None,
    ) -> None:
        self.absolute_max = min(float(absolute_max), ABSOLUTE_MAX_CONFIDENCE)
        self.domain_caps = dict(domain_caps or {})

    def cap_for(self, domain: str = "default") -> float:
        return min(self.absolute_max, self.domain_caps.get(domain, self.absolute_max))

    def apply(self, value: float, domain: str = "default") -> float:
        return apply_confidence_cap(value, self.cap_for(domain))

    def violates_absolute(self, value: float) -> bool:
        return float(value) > self.absolute_max

    def calibrate(self, value: float, domain: str = "default") -> CappedConfidence:
        capped = self.apply(value, domain)
        return CappedConfidence(
            raw=float(value),
            calibrated=capped,
            was_capped=capped < float(value),
        )
