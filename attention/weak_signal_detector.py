"""
Weak Signal Detector — Emerging pattern detection below threshold.

Monitors signals that individually score below the attention threshold but
may be collectively significant.  Uses sliding-window analysis and
cross-domain correlation to surface emerging patterns before they become
full-blown incidents.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from attention.attention_state import AttentionSignal

logger = logging.getLogger(__name__)


class Trend(str, Enum):
    """Direction of an emerging pattern's strength over time."""
    RISING = "rising"
    STABLE = "stable"
    FALLING = "falling"


@dataclass
class EmergingPattern:
    """A cluster of individually-weak signals that form a meaningful pattern."""
    pattern_id: str
    contributing_signals: list[AttentionSignal]
    combined_strength: float
    trend: Trend
    confidence: float
    domains: list[str] = field(default_factory=list)
    description: str = ""
    detected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "contributing_signal_count": len(self.contributing_signals),
            "contributing_signal_ids": [s.signal_id for s in self.contributing_signals],
            "combined_strength": round(self.combined_strength, 4),
            "trend": self.trend.value,
            "confidence": round(self.confidence, 4),
            "domains": self.domains,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
        }


# Pre-defined cross-domain correlation pairs.
# Signals from these domain pairs reinforce each other when co-occurring.
_CORRELATION_PAIRS: list[tuple[str, str]] = [
    ("somatic", "task"),
    ("somatic", "memory"),
    ("governance", "somatic"),
    ("task", "memory"),
    ("external", "governance"),
]


class WeakSignalDetector:
    """
    Detects emerging patterns from below-threshold signals.

    Usage::

        detector = WeakSignalDetector(threshold=0.3)
        patterns = detector.detect_emerging(signals, window_seconds=300)
        for p in patterns:
            print(p.description, p.combined_strength)
    """

    def __init__(
        self,
        threshold: float = 0.30,
        min_cluster_size: int = 3,
        correlation_boost: float = 0.15,
    ) -> None:
        self._threshold = threshold
        self._min_cluster_size = min_cluster_size
        self._correlation_boost = correlation_boost
        self._previous_strengths: dict[str, list[float]] = defaultdict(list)

    def detect_emerging(
        self,
        signals: list[AttentionSignal],
        window_seconds: int = 300,
    ) -> list[EmergingPattern]:
        """
        Scan *signals* within a sliding window and return emerging patterns.

        Only signals whose ``raw_value`` is below ``threshold`` are considered
        "weak".  They are clustered by ``signal_type`` and cross-correlated
        across domains.
        """
        now = datetime.now(timezone.utc)
        cutoff_ts = now.timestamp() - window_seconds

        weak = [
            s for s in signals
            if s.raw_value < self._threshold
            and s.timestamp.timestamp() >= cutoff_ts
        ]

        if len(weak) < self._min_cluster_size:
            return []

        type_clusters = self._cluster_by_type(weak)
        domain_clusters = self._cluster_by_domain_pair(weak)

        patterns: list[EmergingPattern] = []
        patterns.extend(self._evaluate_type_clusters(type_clusters))
        patterns.extend(self._evaluate_domain_clusters(domain_clusters))

        self._update_history(patterns)

        patterns.sort(key=lambda p: p.combined_strength, reverse=True)

        logger.debug(
            "Weak-signal scan: %d weak signals → %d emerging patterns",
            len(weak), len(patterns),
        )
        return patterns

    # ------------------------------------------------------------------
    # Clustering helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cluster_by_type(
        signals: list[AttentionSignal],
    ) -> dict[str, list[AttentionSignal]]:
        clusters: dict[str, list[AttentionSignal]] = defaultdict(list)
        for s in signals:
            clusters[s.signal_type].append(s)
        return clusters

    @staticmethod
    def _cluster_by_domain_pair(
        signals: list[AttentionSignal],
    ) -> dict[tuple[str, str], list[AttentionSignal]]:
        by_domain: dict[str, list[AttentionSignal]] = defaultdict(list)
        for s in signals:
            by_domain[s.source_domain].append(s)

        clusters: dict[tuple[str, str], list[AttentionSignal]] = {}
        for d1, d2 in _CORRELATION_PAIRS:
            if d1 in by_domain and d2 in by_domain:
                combined = by_domain[d1] + by_domain[d2]
                if combined:
                    clusters[(d1, d2)] = combined
        return clusters

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _evaluate_type_clusters(
        self,
        clusters: dict[str, list[AttentionSignal]],
    ) -> list[EmergingPattern]:
        patterns: list[EmergingPattern] = []
        for sig_type, group in clusters.items():
            if len(group) < self._min_cluster_size:
                continue

            strength = self._combined_strength(group)
            domains = sorted({s.source_domain for s in group})
            cross_domain = len(domains) > 1
            if cross_domain:
                strength = min(1.0, strength + self._correlation_boost)

            confidence = min(1.0, len(group) / (self._min_cluster_size * 3))
            trend = self._compute_trend(sig_type, strength)

            patterns.append(EmergingPattern(
                pattern_id=uuid.uuid4().hex,
                contributing_signals=group,
                combined_strength=strength,
                trend=trend,
                confidence=confidence,
                domains=domains,
                description=(
                    f"Emerging cluster of {len(group)} weak '{sig_type}' signals "
                    f"across {', '.join(domains)}"
                ),
            ))
        return patterns

    def _evaluate_domain_clusters(
        self,
        clusters: dict[tuple[str, str], list[AttentionSignal]],
    ) -> list[EmergingPattern]:
        patterns: list[EmergingPattern] = []
        for (d1, d2), group in clusters.items():
            if len(group) < self._min_cluster_size:
                continue

            strength = min(
                1.0,
                self._combined_strength(group) + self._correlation_boost,
            )
            pair_key = f"{d1}+{d2}"
            trend = self._compute_trend(pair_key, strength)
            confidence = min(1.0, len(group) / (self._min_cluster_size * 3))

            patterns.append(EmergingPattern(
                pattern_id=uuid.uuid4().hex,
                contributing_signals=group,
                combined_strength=strength,
                trend=trend,
                confidence=confidence,
                domains=[d1, d2],
                description=(
                    f"Cross-domain correlation between '{d1}' and '{d2}' "
                    f"({len(group)} weak signals)"
                ),
            ))
        return patterns

    # ------------------------------------------------------------------
    # Strength / trend helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _combined_strength(signals: list[AttentionSignal]) -> float:
        """Aggregate weak signals using RMS to reward co-occurrence."""
        if not signals:
            return 0.0
        sum_sq = sum(s.raw_value ** 2 for s in signals)
        return min(1.0, (sum_sq / len(signals)) ** 0.5 * len(signals) ** 0.25)

    def _compute_trend(self, key: str, current_strength: float) -> Trend:
        """Compare current strength to recent history for the same key."""
        history = self._previous_strengths.get(key, [])
        if len(history) < 2:
            return Trend.STABLE

        avg_recent = sum(history[-3:]) / min(len(history), 3)
        delta = current_strength - avg_recent
        if delta > 0.05:
            return Trend.RISING
        if delta < -0.05:
            return Trend.FALLING
        return Trend.STABLE

    def _update_history(self, patterns: list[EmergingPattern]) -> None:
        """Record strengths for trend analysis across calls."""
        for p in patterns:
            key = p.domains[0] if len(p.domains) == 1 else "+".join(p.domains)
            self._previous_strengths[key].append(p.combined_strength)
            if len(self._previous_strengths[key]) > 20:
                self._previous_strengths[key] = self._previous_strengths[key][-20:]
