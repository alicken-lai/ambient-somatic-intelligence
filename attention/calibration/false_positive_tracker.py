"""
False-positive tracker — penalises overconfident, low-uncertainty signals.

A signal that is asserted with high confidence *and* a narrow uncertainty band
is a false-positive risk: it claims near-certainty.  The tracker records such
events per domain and pulls down future confidence for domains with a high
false-positive rate.  Adjusted confidence is always capped below certainty.
"""

from __future__ import annotations

from typing import Any

from attention.calibration.confidence_cap import apply_confidence_cap


class FalsePositiveTracker:
    """Tracks and penalises false-positive-prone confidence assertions."""

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        band_threshold: float = 0.2,
        penalty_scale: float = 0.5,
    ) -> None:
        self.confidence_threshold = float(confidence_threshold)
        self.band_threshold = float(band_threshold)
        self.penalty_scale = float(penalty_scale)
        self._records: list[dict[str, Any]] = []

    def is_false_positive(self, confidence: float, band_width: float) -> bool:
        """A high-confidence, narrow-band assertion is a false-positive risk."""
        return (
            float(confidence) >= self.confidence_threshold
            and float(band_width) <= self.band_threshold
        )

    def record(
        self,
        domain: str,
        pattern_id: str,
        confidence: float,
        band_width: float,
    ) -> bool:
        """Record an assertion; returns whether it was flagged false-positive."""
        is_fp = self.is_false_positive(confidence, band_width)
        self._records.append({
            "domain": domain,
            "pattern_id": pattern_id,
            "confidence": float(confidence),
            "band_width": float(band_width),
            "is_fp": is_fp,
        })
        return is_fp

    def fp_rate(self, domain: str | None = None) -> float:
        """Fraction of records flagged false-positive (optionally per domain)."""
        records = (
            self._records
            if domain is None
            else [r for r in self._records if r["domain"] == domain]
        )
        if not records:
            return 0.0
        return sum(1 for r in records if r["is_fp"]) / len(records)

    def confidence_penalty(self, domain: str | None = None) -> float:
        """Penalty in ``[0, 1]`` derived from the false-positive rate."""
        return max(0.0, min(1.0, self.fp_rate(domain) * self.penalty_scale))

    def adjusted_confidence(self, raw: float, domain: str = "default") -> float:
        """Reduce *raw* by the domain's false-positive penalty, then cap it."""
        penalty = self.confidence_penalty(domain)
        return apply_confidence_cap(float(raw) * (1.0 - penalty))
