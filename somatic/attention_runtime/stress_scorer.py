"""
Runtime Stress Scorer — Aggregate stress scoring from multiple sources.

Computes a composite stress score by combining:
  - Somatic signal pressure (from SignalAnalytics health_score)
  - Memory pressure (from EnvironmentMonitor)
  - Task queue depth
  - Failure rate (from RateTracker)
  - Governance escalation frequency

Provides per-subsystem stress breakdowns and trend analysis.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StressLevel(str, Enum):
    """Categorical stress level."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class StressTrend(str, Enum):
    """Stress trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


@dataclass
class StressScore:
    """Aggregate stress score with component breakdown."""
    overall: float
    components: dict[str, float]
    level: StressLevel
    trend: StressTrend
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": round(self.overall, 4),
            "components": {k: round(v, 4) for k, v in self.components.items()},
            "level": self.level.value,
            "trend": self.trend.value,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


@dataclass
class StressMap:
    """Per-subsystem stress breakdown."""
    subsystem_scores: dict[str, float]
    hotspots: list[str]
    recommendations: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_scores": {
                k: round(v, 4) for k, v in self.subsystem_scores.items()
            },
            "hotspots": self.hotspots,
            "recommendations": self.recommendations,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class RuntimeStressScorer:
    """
    Computes aggregate runtime stress from multiple subsystem sources.

    Usage:
        scorer = RuntimeStressScorer()
        scorer.set_signal_analytics(analytics)
        scorer.set_environment_monitor(monitor)
        scorer.set_rate_tracker(tracker)

        stress = scorer.compute_stress()
        stress_map = scorer.get_stress_map()
    """

    WEIGHT_SOMATIC = 0.30
    WEIGHT_MEMORY = 0.20
    WEIGHT_TASK_QUEUE = 0.15
    WEIGHT_FAILURE_RATE = 0.20
    WEIGHT_GOVERNANCE = 0.15

    def __init__(self):
        self._signal_analytics: Any = None
        self._environment_monitor: Any = None
        self._rate_tracker: Any = None
        self._task_queue_depth: int = 0
        self._governance_escalation_count: int = 0
        self._history: list[StressScore] = []
        self._max_history = 100

    def set_signal_analytics(self, analytics: Any) -> None:
        """Set the SignalAnalytics instance for somatic pressure scoring."""
        self._signal_analytics = analytics

    def set_environment_monitor(self, monitor: Any) -> None:
        """Set the EnvironmentMonitor for memory/system pressure."""
        self._environment_monitor = monitor

    def set_rate_tracker(self, tracker: Any) -> None:
        """Set the RateTracker for failure rate assessment."""
        self._rate_tracker = tracker

    def set_task_queue_depth(self, depth: int) -> None:
        """Update current task queue depth."""
        self._task_queue_depth = max(0, depth)

    def set_governance_escalation_count(self, count: int) -> None:
        """Update governance escalation count."""
        self._governance_escalation_count = max(0, count)

    def compute_stress(self) -> StressScore:
        """
        Compute aggregate stress score from all registered sources.

        Returns a StressScore with overall 0.0-1.0, component breakdown,
        categorical level, and trend direction.
        """
        somatic = self._compute_somatic_pressure()
        memory = self._compute_memory_pressure()
        task_queue = self._compute_task_queue_pressure()
        failure = self._compute_failure_rate_pressure()
        governance = self._compute_governance_pressure()

        components = {
            "somatic_pressure": somatic,
            "memory_pressure": memory,
            "task_queue_pressure": task_queue,
            "failure_rate": failure,
            "governance_escalation": governance,
        }

        overall = (
            self.WEIGHT_SOMATIC * somatic
            + self.WEIGHT_MEMORY * memory
            + self.WEIGHT_TASK_QUEUE * task_queue
            + self.WEIGHT_FAILURE_RATE * failure
            + self.WEIGHT_GOVERNANCE * governance
        )
        overall = max(0.0, min(1.0, overall))

        level = self._classify_level(overall)
        trend = self._compute_trend()

        score = StressScore(
            overall=overall,
            components=components,
            level=level,
            trend=trend,
        )

        self._history.append(score)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        logger.debug(
            "Stress computed: overall=%.3f level=%s trend=%s",
            overall, level.value, trend.value,
        )
        return score

    def get_stress_map(self) -> StressMap:
        """Get per-subsystem stress breakdown with hotspots."""
        score = self._history[-1] if self._history else self.compute_stress()

        subsystem_scores: dict[str, float] = {}
        subsystem_scores["somatic"] = score.components.get("somatic_pressure", 0.0)
        subsystem_scores["environment"] = score.components.get("memory_pressure", 0.0)
        subsystem_scores["task_scheduler"] = score.components.get("task_queue_pressure", 0.0)
        subsystem_scores["error_handling"] = score.components.get("failure_rate", 0.0)
        subsystem_scores["governance"] = score.components.get("governance_escalation", 0.0)

        hotspots = [
            name for name, val in subsystem_scores.items()
            if val > 0.6
        ]
        hotspots.sort(key=lambda n: subsystem_scores[n], reverse=True)

        recommendations = self._generate_recommendations(subsystem_scores, hotspots)

        return StressMap(
            subsystem_scores=subsystem_scores,
            hotspots=hotspots,
            recommendations=recommendations,
        )

    def _compute_somatic_pressure(self) -> float:
        """Derive stress from SignalAnalytics health_score (inverted)."""
        if not self._signal_analytics:
            return 0.0
        try:
            health = self._signal_analytics.health_score()
            return max(0.0, 1.0 - health)
        except Exception:
            return 0.0

    def _compute_memory_pressure(self) -> float:
        """Derive stress from EnvironmentMonitor metrics."""
        if not self._environment_monitor:
            return 0.0
        try:
            snapshot = self._environment_monitor.last_snapshot
            if not snapshot:
                return 0.0
            mem_pressure = snapshot.memory_percent / 100.0
            cpu_pressure = snapshot.cpu_percent / 100.0
            return max(0.0, min(1.0, max(mem_pressure, cpu_pressure)))
        except Exception:
            return 0.0

    def _compute_task_queue_pressure(self) -> float:
        """Derive stress from task queue depth."""
        if self._task_queue_depth <= 0:
            return 0.0
        return min(self._task_queue_depth / 20.0, 1.0)

    def _compute_failure_rate_pressure(self) -> float:
        """Derive stress from RateTracker failure rates."""
        if not self._rate_tracker:
            return 0.0
        try:
            from somatic.signal_bus import SignalType
            pain_rate = self._rate_tracker.current_rate(SignalType.PAIN)
            is_spike = self._rate_tracker.is_spike(SignalType.PAIN)

            pressure = min(pain_rate / 30.0, 1.0)
            if is_spike:
                pressure = min(pressure * 1.5, 1.0)
            return pressure
        except Exception:
            return 0.0

    def _compute_governance_pressure(self) -> float:
        """Derive stress from governance escalation frequency."""
        if self._governance_escalation_count <= 0:
            return 0.0
        return min(self._governance_escalation_count / 10.0, 1.0)

    def _classify_level(self, overall: float) -> StressLevel:
        """Classify stress into categorical levels."""
        if overall > 0.8:
            return StressLevel.CRITICAL
        elif overall > 0.6:
            return StressLevel.HIGH
        elif overall > 0.3:
            return StressLevel.MODERATE
        return StressLevel.LOW

    def _compute_trend(self) -> StressTrend:
        """Compute stress trend from history."""
        if len(self._history) < 3:
            return StressTrend.STABLE

        recent = self._history[-6:]
        mid = len(recent) // 2
        first_avg = sum(s.overall for s in recent[:mid]) / mid
        second_avg = sum(s.overall for s in recent[mid:]) / (len(recent) - mid)

        diff = second_avg - first_avg
        if diff > 0.05:
            return StressTrend.DEGRADING
        elif diff < -0.05:
            return StressTrend.IMPROVING
        return StressTrend.STABLE

    @staticmethod
    def _generate_recommendations(
        scores: dict[str, float],
        hotspots: list[str],
    ) -> list[str]:
        """Generate recommendations based on stress distribution."""
        recs: list[str] = []

        if "somatic" in hotspots:
            recs.append("Somatic subsystem under pressure — review signal volume and sources")
        if "environment" in hotspots:
            recs.append("System resources strained — consider scaling or load shedding")
        if "task_scheduler" in hotspots:
            recs.append("Task queue depth high — throttle task intake or increase processing capacity")
        if "error_handling" in hotspots:
            recs.append("Elevated failure rate — investigate error sources and apply circuit breakers")
        if "governance" in hotspots:
            recs.append("Frequent governance escalations — review escalation thresholds")

        if not recs:
            recs.append("Stress levels within normal parameters")

        return recs
