"""Detect accumulating doctrine drift across runtime soak windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.doctrine_drift_detector import DoctrineDriftDetector


@dataclass
class DriftAccumulationVerdict:
    drift_bounded: bool
    cumulative_drift: float
    window_count: int
    spikes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "drift_bounded": self.drift_bounded,
            "cumulative_drift": round(self.cumulative_drift, 4),
            "window_count": self.window_count,
            "spikes": list(self.spikes),
        }


class DriftAccumulationDetector:
    """Track drift samples over soak horizons; bounded if cumulative < 0.35."""

    _DRIFT_CEILING = 0.35

    def __init__(self) -> None:
        self._detector = DoctrineDriftDetector()
        self._samples: list[float] = []

    def ingest(self, text: str) -> float:
        verdict = self._detector.compare(text)
        score = 1.0 - verdict.overlap_ratio if verdict.drift_detected else verdict.overlap_ratio
        self._samples.append(score)
        return score

    def evaluate(self) -> DriftAccumulationVerdict:
        if not self._samples:
            return DriftAccumulationVerdict(
                drift_bounded=True,
                cumulative_drift=0.0,
                window_count=0,
            )
        cumulative = sum(self._samples) / len(self._samples)
        spikes = [
            f"sample_{i}"
            for i, s in enumerate(self._samples)
            if s > self._DRIFT_CEILING
        ]
        return DriftAccumulationVerdict(
            drift_bounded=cumulative < self._DRIFT_CEILING and len(spikes) <= 1,
            cumulative_drift=cumulative,
            window_count=len(self._samples),
            spikes=spikes,
        )
