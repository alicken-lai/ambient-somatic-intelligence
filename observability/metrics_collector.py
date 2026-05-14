"""
Metrics Collector — Unified metrics aggregation for the Ambient OS.

Collects and aggregates metrics across all layers:
  - Token usage (budget consumption, waste, compression savings)
  - Memory operations (recalls, stores, TTL expirations, hit rates)
  - Governance decisions (allow/block/review counts, policy hits)
  - Task execution (success/failure rates, durations, retries)
  - Somatic signals (signal rates, attention levels, response triggers)
  - Context assembly (budget utilization, compression ratios)

Supports:
  - Counter (monotonically increasing)
  - Gauge (current value)
  - Histogram (distribution tracking)
  - Rate (events per second over window)
"""

from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


METRICS_DIR = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os")) / "observability" / "metrics"


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    type: MetricType
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class HistogramBucket:
    """Tracks value distribution."""
    values: list[float] = field(default_factory=list)
    max_samples: int = 1000

    def record(self, value: float) -> None:
        self.values.append(value)
        if len(self.values) > self.max_samples:
            self.values = self.values[-self.max_samples:]

    @property
    def count(self) -> int:
        return len(self.values)

    @property
    def sum(self) -> float:
        return sum(self.values) if self.values else 0

    @property
    def avg(self) -> float:
        return self.sum / self.count if self.count else 0

    @property
    def min(self) -> float:
        return min(self.values) if self.values else 0

    @property
    def max(self) -> float:
        return max(self.values) if self.values else 0

    @property
    def p50(self) -> float:
        return self._percentile(50)

    @property
    def p95(self) -> float:
        return self._percentile(95)

    @property
    def p99(self) -> float:
        return self._percentile(99)

    def _percentile(self, p: float) -> float:
        if not self.values:
            return 0
        sorted_vals = sorted(self.values)
        idx = int(len(sorted_vals) * p / 100)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "sum": round(self.sum, 2),
            "avg": round(self.avg, 2),
            "min": round(self.min, 2),
            "max": round(self.max, 2),
            "p50": round(self.p50, 2),
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2),
        }


class MetricsCollector:
    """
    Central metrics collection and aggregation.

    Usage:
        metrics = MetricsCollector()

        # Counters
        metrics.increment("memory.recalls")
        metrics.increment("governance.blocked", tags={"policy": "destructive_cmd"})

        # Gauges
        metrics.gauge("tokens.budget_used", 3500)
        metrics.gauge("attention.level", 2)

        # Histograms
        metrics.histogram("task.duration_ms", 1250)
        metrics.histogram("memory.recall_latency_ms", 45)

        # Query
        report = metrics.report()
        token_stats = metrics.get_histogram("task.duration_ms")
    """

    def __init__(self, persist: bool = True, flush_interval: int = 60):
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, HistogramBucket] = {}
        self._rates: dict[str, deque] = {}
        self._tags: dict[str, dict[str, str]] = {}
        self._last_flush: float = time.time()
        self._flush_interval = flush_interval
        self._persist = persist

        if persist:
            METRICS_DIR.mkdir(parents=True, exist_ok=True)

    def increment(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        self._counters[name] = self._counters.get(name, 0) + value
        if tags:
            self._tags[name] = tags
        self._record_rate(name)
        self._maybe_flush()

    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Set a gauge metric to current value."""
        self._gauges[name] = value
        if tags:
            self._tags[name] = tags

    def histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram value."""
        if name not in self._histograms:
            self._histograms[name] = HistogramBucket()
        self._histograms[name].record(value)
        if tags:
            self._tags[name] = tags

    def get_counter(self, name: str) -> float:
        """Get current counter value."""
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float | None:
        """Get current gauge value."""
        return self._gauges.get(name)

    def get_histogram(self, name: str) -> dict[str, Any] | None:
        """Get histogram statistics."""
        h = self._histograms.get(name)
        return h.to_dict() if h else None

    def get_rate(self, name: str, window_seconds: float = 60) -> float:
        """Get events per second over window."""
        events = self._rates.get(name)
        if not events:
            return 0.0
        cutoff = time.time() - window_seconds
        recent = [t for t in events if t >= cutoff]
        return len(recent) / window_seconds if window_seconds > 0 else 0.0

    def report(self) -> dict[str, Any]:
        """Generate full metrics report."""
        return {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: v.to_dict() for k, v in self._histograms.items()},
            "rates": {k: round(self.get_rate(k), 3) for k in self._rates},
        }

    def report_by_layer(self) -> dict[str, dict[str, Any]]:
        """Generate report grouped by system layer."""
        layers: dict[str, dict[str, Any]] = {
            "token": {},
            "memory": {},
            "governance": {},
            "task": {},
            "somatic": {},
            "context": {},
            "agent": {},
            "other": {},
        }

        all_metrics = {}
        for name, value in self._counters.items():
            all_metrics[name] = {"type": "counter", "value": value}
        for name, value in self._gauges.items():
            all_metrics[name] = {"type": "gauge", "value": value}
        for name, bucket in self._histograms.items():
            all_metrics[name] = {"type": "histogram", **bucket.to_dict()}

        for name, data in all_metrics.items():
            prefix = name.split(".")[0] if "." in name else "other"
            target = layers.get(prefix, layers["other"])
            target[name] = data

        return {k: v for k, v in layers.items() if v}

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._rates.clear()

    def _record_rate(self, name: str) -> None:
        if name not in self._rates:
            self._rates[name] = deque(maxlen=1000)
        self._rates[name].append(time.time())

    def _maybe_flush(self) -> None:
        """Periodically persist metrics to disk."""
        now = time.time()
        if self._persist and (now - self._last_flush) >= self._flush_interval:
            self._flush()
            self._last_flush = now

    def _flush(self) -> None:
        """Write current metrics to disk."""
        try:
            filepath = METRICS_DIR / "metrics_latest.json"
            with open(filepath, "w") as f:
                json.dump(self.report(), f, indent=2)
        except OSError:
            pass
