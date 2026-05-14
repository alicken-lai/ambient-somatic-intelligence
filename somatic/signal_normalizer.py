"""
Signal Normalizer — Adaptive baseline normalization for somatic signals.

Transforms raw metric values into 0.0–1.0 severity scores by learning
each source's baseline via exponential moving average (EMA). This
eliminates false positives from systems that consistently run hot:

  - A machine that idles at 60% CPU treats 60% as 0.0 severity
  - A sudden jump from 60% to 90% maps to ~0.8 severity
  - Sustained 90% slowly shifts the baseline upward (adaptation)

The normalizer maintains per-source state and requires no external
configuration — it learns from the traffic it sees.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaselineState:
    """Per-source learned baseline statistics."""
    source: str
    ema_mean: float = 0.0
    ema_variance: float = 1.0
    sample_count: int = 0
    last_updated: float = field(default_factory=time.time)

    @property
    def std_dev(self) -> float:
        return max(math.sqrt(abs(self.ema_variance)), 1e-6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "ema_mean": round(self.ema_mean, 4),
            "ema_variance": round(self.ema_variance, 4),
            "std_dev": round(self.std_dev, 4),
            "sample_count": self.sample_count,
            "last_updated": self.last_updated,
        }


@dataclass
class NormalizedSignal:
    """A signal with severity normalized to 0.0–1.0."""
    source: str
    raw_value: float
    severity: float
    z_score: float
    baseline_mean: float
    baseline_std: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "raw_value": round(self.raw_value, 4),
            "severity": round(self.severity, 4),
            "z_score": round(self.z_score, 4),
            "baseline_mean": round(self.baseline_mean, 4),
            "baseline_std": round(self.baseline_std, 4),
            "timestamp": self.timestamp,
        }


class SignalNormalizer:
    """
    Maintains rolling baselines per signal source and normalizes
    raw values into 0.0–1.0 severity.

    Usage:
        normalizer = SignalNormalizer()
        result = normalizer.normalize("cpu", 85.0)
        # result.severity ~ 0.0 initially (first sample is baseline)

        # After many samples around 50%, a jump to 85% yields high severity
        for _ in range(20):
            normalizer.normalize("cpu", 50.0)
        result = normalizer.normalize("cpu", 85.0)
        # result.severity ~ 0.9
    """

    def __init__(
        self,
        alpha: float = 0.1,
        severity_cap_z: float = 3.0,
        min_samples_for_baseline: int = 5,
    ):
        self._alpha = alpha
        self._severity_cap_z = severity_cap_z
        self._min_samples = min_samples_for_baseline
        self._baselines: dict[str, BaselineState] = {}

    def normalize(self, source: str, value: float) -> NormalizedSignal:
        """
        Normalize a raw value against the learned baseline for this source.

        Updates the baseline EMA as a side effect.
        """
        baseline = self._get_or_create_baseline(source)
        self._update_baseline(baseline, value)

        if baseline.sample_count < self._min_samples:
            z_score = 0.0
        else:
            z_score = (value - baseline.ema_mean) / baseline.std_dev

        severity = self._z_to_severity(z_score)

        return NormalizedSignal(
            source=source,
            raw_value=value,
            severity=severity,
            z_score=z_score,
            baseline_mean=baseline.ema_mean,
            baseline_std=baseline.std_dev,
        )

    def update_baseline(self, source: str, value: float) -> None:
        """Explicitly update baseline without producing a normalized signal."""
        baseline = self._get_or_create_baseline(source)
        self._update_baseline(baseline, value)

    def get_baseline(self, source: str) -> BaselineState | None:
        """Retrieve current baseline state for a source."""
        return self._baselines.get(source)

    def all_baselines(self) -> dict[str, dict[str, Any]]:
        """Return all baselines as serializable dicts."""
        return {k: v.to_dict() for k, v in self._baselines.items()}

    def reset(self, source: str | None = None) -> None:
        """Reset baseline(s). If source is None, reset all."""
        if source is None:
            self._baselines.clear()
        else:
            self._baselines.pop(source, None)

    def _get_or_create_baseline(self, source: str) -> BaselineState:
        if source not in self._baselines:
            self._baselines[source] = BaselineState(source=source)
        return self._baselines[source]

    def _update_baseline(self, baseline: BaselineState, value: float) -> None:
        """Update EMA mean and variance with a new observation."""
        baseline.sample_count += 1
        baseline.last_updated = time.time()

        if baseline.sample_count == 1:
            baseline.ema_mean = value
            baseline.ema_variance = 0.0
            return

        alpha = self._alpha
        diff = value - baseline.ema_mean
        baseline.ema_mean += alpha * diff
        baseline.ema_variance = (1 - alpha) * (baseline.ema_variance + alpha * diff * diff)

    def _z_to_severity(self, z: float) -> float:
        """Map z-score to 0.0–1.0 severity using sigmoid-like clamping."""
        if z <= 0:
            return 0.0
        normalized = z / self._severity_cap_z
        return min(normalized, 1.0)
