"""
Recursive Telemetry — The system observing its own observation.

Meta-level telemetry that monitors the health and cost of the
observability stack itself:
  - Tracer health (traces/min, avg span duration, buffer pressure)
  - Metrics collector health (metric count, staleness)
  - Telemetry pipeline latency
  - Dashboard render time
  - Audit log growth rate
  - Observability overhead (% of system resources spent on observation)

Ensures the observability layer remains lightweight and does not
become a system bottleneck.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TracerHealth:
    """Health metrics for the execution tracer."""
    traces_per_minute: float = 0.0
    avg_span_duration_ms: float = 0.0
    active_spans: int = 0
    buffer_utilization: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "traces_per_minute": round(self.traces_per_minute, 2),
            "avg_span_duration_ms": round(self.avg_span_duration_ms, 2),
            "active_spans": self.active_spans,
            "buffer_utilization": round(self.buffer_utilization, 4),
        }


@dataclass
class MetricsHealth:
    """Health metrics for the metrics collector."""
    metric_count: int = 0
    counter_count: int = 0
    gauge_count: int = 0
    histogram_count: int = 0
    staleness_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "metric_count": self.metric_count,
            "counter_count": self.counter_count,
            "gauge_count": self.gauge_count,
            "histogram_count": self.histogram_count,
            "staleness_seconds": round(self.staleness_seconds, 1),
        }


@dataclass
class RecursiveTelemetryReport:
    """Complete recursive telemetry report."""
    tracer_health: TracerHealth = field(default_factory=TracerHealth)
    metrics_health: MetricsHealth = field(default_factory=MetricsHealth)
    pipeline_latency_ms: float = 0.0
    overhead_pct: float = 0.0
    staleness: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(tz=timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "tracer_health": self.tracer_health.to_dict(),
            "metrics_health": self.metrics_health.to_dict(),
            "pipeline_latency_ms": round(self.pipeline_latency_ms, 2),
            "overhead_pct": round(self.overhead_pct, 4),
            "staleness": round(self.staleness, 1),
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class RecursiveTelemetry:
    """
    Meta-level telemetry — the system observing its own observation.

    Monitors the observability stack itself to ensure it remains
    lightweight, healthy, and not a system bottleneck.

    Usage:
        from observability.tracer import ExecutionTracer
        from observability.metrics_collector import MetricsCollector

        tracer = ExecutionTracer()
        metrics = MetricsCollector()

        recursive = RecursiveTelemetry(tracer=tracer, metrics=metrics)
        report = recursive.collect()
        print(f"Observability overhead: {report.overhead_pct:.2f}%")
        print(f"Healthy: {recursive.is_healthy()}")
    """

    def __init__(
        self,
        tracer: Any | None = None,
        metrics: Any | None = None,
        telemetry: Any | None = None,
        overhead_threshold_pct: float = 5.0,
        latency_threshold_ms: float = 50.0,
    ):
        self._tracer = tracer
        self._metrics = metrics
        self._telemetry = telemetry
        self._overhead_threshold_pct = overhead_threshold_pct
        self._latency_threshold_ms = latency_threshold_ms
        self._collection_times: list[float] = []
        self._last_collection: float = 0.0

    def collect(self) -> RecursiveTelemetryReport:
        """
        Gather telemetry from all observability components.

        Measures:
          - Tracer health (traces/min, avg span duration)
          - Metrics collector health (metric count, staleness)
          - Pipeline latency (how long this collection takes)
          - Overhead (% of system resources used by observability)
        """
        start = time.time()

        tracer_health = self._collect_tracer_health()
        metrics_health = self._collect_metrics_health()
        pipeline_latency = self._measure_pipeline_latency(start)
        overhead = self.get_observability_overhead()

        recommendations = self._generate_recommendations(
            tracer_health, metrics_health, pipeline_latency, overhead
        )

        elapsed = (time.time() - start) * 1000
        self._collection_times.append(elapsed)
        if len(self._collection_times) > 100:
            self._collection_times = self._collection_times[-100:]
        self._last_collection = time.time()

        report = RecursiveTelemetryReport(
            tracer_health=tracer_health,
            metrics_health=metrics_health,
            pipeline_latency_ms=elapsed,
            overhead_pct=overhead,
            staleness=time.time() - self._last_collection if self._last_collection else 0.0,
            recommendations=recommendations,
        )

        logger.debug(
            "Recursive telemetry collected: overhead=%.2f%% latency=%.1fms",
            overhead, elapsed
        )
        return report

    def get_observability_overhead(self) -> float:
        """
        Estimate how much the observability layer costs as a % of system resources.

        Based on collection time relative to the interval between collections.
        """
        if not self._collection_times:
            return 0.0

        avg_collection_ms = sum(self._collection_times) / len(self._collection_times)
        # Assume system cycle is roughly 1 second
        overhead_pct = (avg_collection_ms / 1000.0) * 100.0
        return min(100.0, overhead_pct)

    def is_healthy(self) -> bool:
        """
        Quick health check of the observability stack itself.

        Returns True if overhead is below threshold and pipeline latency is acceptable.
        """
        overhead = self.get_observability_overhead()
        if overhead > self._overhead_threshold_pct:
            return False

        if self._collection_times:
            latest_latency = self._collection_times[-1]
            if latest_latency > self._latency_threshold_ms:
                return False

        return True

    def _collect_tracer_health(self) -> TracerHealth:
        """Collect health metrics from the execution tracer."""
        if self._tracer is None:
            return TracerHealth()

        stats = {}
        try:
            stats = self._tracer.stats()
        except Exception:
            logger.warning("Failed to collect tracer stats")
            return TracerHealth()

        total_traces = stats.get("total_traces", 0)
        avg_duration = stats.get("avg_duration_ms", 0.0)

        # Estimate traces per minute based on recent activity
        traces_per_minute = 0.0
        if hasattr(self._tracer, "_completed_traces") and self._tracer._completed_traces:
            recent = self._tracer._completed_traces[-10:]
            if len(recent) >= 2:
                time_span = recent[-1].spans[0].start_time - recent[0].spans[0].start_time
                if time_span > 0:
                    traces_per_minute = (len(recent) / time_span) * 60.0

        buffer_utilization = 0.0
        if hasattr(self._tracer, "_max_traces") and self._tracer._max_traces > 0:
            buffer_utilization = total_traces / self._tracer._max_traces

        return TracerHealth(
            traces_per_minute=traces_per_minute,
            avg_span_duration_ms=avg_duration,
            active_spans=1 if stats.get("active_trace") else 0,
            buffer_utilization=buffer_utilization,
        )

    def _collect_metrics_health(self) -> MetricsHealth:
        """Collect health metrics from the metrics collector."""
        if self._metrics is None:
            return MetricsHealth()

        try:
            report = self._metrics.report()
        except Exception:
            logger.warning("Failed to collect metrics health")
            return MetricsHealth()

        counters = report.get("counters", {})
        gauges = report.get("gauges", {})
        histograms = report.get("histograms", {})

        staleness = 0.0
        if hasattr(self._metrics, "_last_flush"):
            staleness = time.time() - self._metrics._last_flush

        return MetricsHealth(
            metric_count=len(counters) + len(gauges) + len(histograms),
            counter_count=len(counters),
            gauge_count=len(gauges),
            histogram_count=len(histograms),
            staleness_seconds=staleness,
        )

    def _measure_pipeline_latency(self, start: float) -> float:
        """Measure the latency of the telemetry pipeline itself."""
        return (time.time() - start) * 1000

    def _generate_recommendations(
        self,
        tracer_health: TracerHealth,
        metrics_health: MetricsHealth,
        pipeline_latency: float,
        overhead: float,
    ) -> list[str]:
        """Generate actionable recommendations based on telemetry state."""
        recommendations = []

        if overhead > self._overhead_threshold_pct:
            recommendations.append(
                f"Observability overhead ({overhead:.1f}%) exceeds threshold "
                f"({self._overhead_threshold_pct:.1f}%). Consider reducing trace verbosity."
            )

        if tracer_health.buffer_utilization > 0.9:
            recommendations.append(
                "Trace buffer near capacity. Consider increasing max_traces or "
                "implementing trace sampling."
            )

        if metrics_health.staleness_seconds > 300:
            recommendations.append(
                f"Metrics staleness ({metrics_health.staleness_seconds:.0f}s) is high. "
                "Check if flush interval is appropriate."
            )

        if pipeline_latency > self._latency_threshold_ms:
            recommendations.append(
                f"Pipeline latency ({pipeline_latency:.1f}ms) exceeds threshold. "
                "Consider async collection or reducing metric cardinality."
            )

        return recommendations
