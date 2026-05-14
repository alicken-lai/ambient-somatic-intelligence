"""
Signal Analytics — Analytical queries over somatic signal history.

Provides aggregate views over the SignalBus history:

  - summary():      counts, distribution, urgency breakdown per time window
  - top_sources():  most active signal sources
  - trend():        directional trend for a signal type
  - health_score(): 0.0 (critical) to 1.0 (healthy) composite score

The analytics layer is read-only — it never emits signals, only
interprets the history that the bus already maintains.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType, SignalUrgency


@dataclass
class AnalyticsSummary:
    """Aggregated analytics over a time window."""
    window_seconds: float
    total_signals: int
    by_type: dict[str, int]
    by_urgency: dict[str, int]
    unique_sources: int
    avg_urgency: float
    critical_ratio: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_seconds": self.window_seconds,
            "total_signals": self.total_signals,
            "by_type": self.by_type,
            "by_urgency": self.by_urgency,
            "unique_sources": self.unique_sources,
            "avg_urgency": round(self.avg_urgency, 2),
            "critical_ratio": round(self.critical_ratio, 4),
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


@dataclass
class HealthReport:
    """Comprehensive somatic health assessment."""
    score: float
    grade: str
    factors: dict[str, float]
    recommendations: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "grade": self.grade,
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "recommendations": self.recommendations,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class SignalAnalytics:
    """
    Analytical query engine over the SignalBus history.

    Usage:
        bus = SomaticSignalBus()
        analytics = SignalAnalytics(bus)

        summary = analytics.summary(window_seconds=300)
        top = analytics.top_sources(n=5)
        trend = analytics.trend(SignalType.PRESSURE, window_seconds=600)
        score = analytics.health_score()
    """

    def __init__(self, bus: SomaticSignalBus | None = None):
        self.bus = bus or SomaticSignalBus()

    def summary(self, window_seconds: float = 300) -> AnalyticsSummary:
        """Get aggregate statistics over a time window."""
        signals = self.bus.recent(seconds=window_seconds)

        by_type: dict[str, int] = {t.value: 0 for t in SignalType}
        by_urgency: dict[str, int] = {}
        sources: set[str] = set()
        urgency_sum = 0.0

        for s in signals:
            by_type[s.type.value] = by_type.get(s.type.value, 0) + 1
            urg_name = SignalUrgency(s.urgency).name
            by_urgency[urg_name] = by_urgency.get(urg_name, 0) + 1
            sources.add(s.source)
            urgency_sum += int(s.urgency)

        total = len(signals)
        critical_count = sum(1 for s in signals if s.is_critical)

        return AnalyticsSummary(
            window_seconds=window_seconds,
            total_signals=total,
            by_type=by_type,
            by_urgency=by_urgency,
            unique_sources=len(sources),
            avg_urgency=urgency_sum / total if total else 0.0,
            critical_ratio=critical_count / total if total else 0.0,
        )

    def top_sources(self, n: int = 5, window_seconds: float = 300) -> list[dict[str, Any]]:
        """Get the most active signal sources."""
        signals = self.bus.recent(seconds=window_seconds)
        source_counts: dict[str, int] = {}
        source_urgency: dict[str, list[int]] = {}

        for s in signals:
            source_counts[s.source] = source_counts.get(s.source, 0) + 1
            if s.source not in source_urgency:
                source_urgency[s.source] = []
            source_urgency[s.source].append(int(s.urgency))

        ranked = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:n]

        return [
            {
                "source": src,
                "count": count,
                "avg_urgency": round(
                    sum(source_urgency[src]) / len(source_urgency[src]), 2
                ),
                "max_urgency": max(source_urgency[src]),
            }
            for src, count in ranked
        ]

    def trend(
        self,
        signal_type: SignalType,
        window_seconds: float = 600,
        buckets: int = 6,
    ) -> dict[str, Any]:
        """
        Analyze the trend of a signal type over time.

        Divides the window into buckets and compares rates.
        """
        signals = self.bus.recent(signal_type=signal_type, seconds=window_seconds)

        if len(signals) < 2:
            return {
                "signal_type": signal_type.value,
                "trend": "insufficient_data",
                "total_signals": len(signals),
                "window_seconds": window_seconds,
            }

        now = time.time()
        bucket_size = window_seconds / buckets
        bucket_counts: list[int] = [0] * buckets

        for s in signals:
            age = now - s.timestamp
            bucket_idx = min(int(age / bucket_size), buckets - 1)
            bucket_counts[buckets - 1 - bucket_idx] += 1

        first_half = bucket_counts[: buckets // 2]
        second_half = bucket_counts[buckets // 2:]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        if avg_first == 0 and avg_second == 0:
            direction = "stable"
        elif avg_first == 0:
            direction = "increasing"
        else:
            ratio = avg_second / avg_first
            if ratio > 1.3:
                direction = "increasing"
            elif ratio < 0.7:
                direction = "decreasing"
            else:
                direction = "stable"

        return {
            "signal_type": signal_type.value,
            "trend": direction,
            "total_signals": len(signals),
            "window_seconds": window_seconds,
            "bucket_counts": bucket_counts,
            "avg_first_half": round(avg_first, 2),
            "avg_second_half": round(avg_second, 2),
        }

    def health_score(self) -> float:
        """
        Compute a composite health score from 0.0 (critical) to 1.0 (healthy).

        Factors:
          - Signal volume (fewer = healthier)
          - Critical ratio (lower = healthier)
          - Pain signal presence (fewer = healthier)
          - Calm signal presence (more = healthier)
          - Average urgency (lower = healthier)
        """
        report = self.health_report()
        return report.score

    def health_report(self, window_seconds: float = 300) -> HealthReport:
        """Generate a comprehensive health report."""
        signals = self.bus.recent(seconds=window_seconds)
        total = len(signals)

        if total == 0:
            return HealthReport(
                score=1.0,
                grade="A",
                factors={"volume": 1.0, "critical": 1.0, "pain": 1.0, "calm": 1.0, "urgency": 1.0},
                recommendations=["System is quiet — no recent signals"],
            )

        critical_count = sum(1 for s in signals if s.is_critical)
        pain_count = sum(1 for s in signals if s.type == SignalType.PAIN)
        calm_count = sum(1 for s in signals if s.type == SignalType.CALM)
        pressure_count = sum(1 for s in signals if s.type == SignalType.PRESSURE)
        avg_urgency = sum(int(s.urgency) for s in signals) / total

        volume_factor = max(0.0, 1.0 - (total / 50.0))
        critical_factor = max(0.0, 1.0 - (critical_count / 5.0))
        pain_factor = max(0.0, 1.0 - (pain_count / 10.0))
        calm_factor = min(1.0, 0.5 + (calm_count / (total * 2)))
        urgency_factor = max(0.0, 1.0 - ((avg_urgency - 1.0) / 4.0))

        factors = {
            "volume": volume_factor,
            "critical": critical_factor,
            "pain": pain_factor,
            "calm": calm_factor,
            "urgency": urgency_factor,
        }

        weights = {"volume": 0.15, "critical": 0.30, "pain": 0.25, "calm": 0.10, "urgency": 0.20}
        score = sum(factors[k] * weights[k] for k in factors)
        score = max(0.0, min(1.0, score))

        grade = self._score_to_grade(score)
        recommendations = self._generate_recommendations(
            score, total, critical_count, pain_count, pressure_count, calm_count
        )

        return HealthReport(
            score=score,
            grade=grade,
            factors=factors,
            recommendations=recommendations,
        )

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= 0.9:
            return "A"
        elif score >= 0.75:
            return "B"
        elif score >= 0.55:
            return "C"
        elif score >= 0.35:
            return "D"
        return "F"

    @staticmethod
    def _generate_recommendations(
        score: float,
        total: int,
        critical: int,
        pain: int,
        pressure: int,
        calm: int,
    ) -> list[str]:
        recs: list[str] = []

        if critical > 0:
            recs.append(f"{critical} critical signals detected — investigate immediately")
        if pain > 3:
            recs.append(f"{pain} pain signals — check error logs and failure sources")
        if pressure > 5:
            recs.append(f"{pressure} pressure signals — consider scaling resources")
        if score < 0.4:
            recs.append("System health is poor — recommend throttling non-essential tasks")
        if calm == 0 and total > 5:
            recs.append("No calm signals — system has not recovered recently")
        if not recs:
            recs.append("System is operating within normal parameters")

        return recs
