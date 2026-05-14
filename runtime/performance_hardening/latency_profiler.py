"""Profile and analyze execution latency across system operations."""
from __future__ import annotations

import functools
import logging
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class LatencyRecord:
    operation: str
    duration_ms: float
    timestamp: float
    metadata: dict


@dataclass
class OperationProfile:
    operation: str
    call_count: int
    total_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    trend: str
    last_called: float


@dataclass
class LatencyReport:
    profiles: list[OperationProfile]
    total_operations: int
    slowest_operation: str
    avg_system_latency_ms: float
    bottleneck_candidates: list[str]
    generated_at: str


class OperationTimer:
    def __init__(self, profiler: LatencyProfiler, name: str) -> None:
        self._profiler = profiler
        self._name = name
        self._start: float = 0.0
        self._duration_ms: float = 0.0

    @property
    def duration_ms(self) -> float:
        return self._duration_ms

    def __enter__(self) -> OperationTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed = time.perf_counter() - self._start
        self._duration_ms = elapsed * 1000.0
        self._profiler.record_latency(self._name, self._duration_ms)


class LatencyProfiler:
    MAX_RECORDS_PER_OP = 1000

    def __init__(self) -> None:
        self._records: dict[str, deque[LatencyRecord]] = {}

    def profile_operation(self, name: str) -> OperationTimer:
        return OperationTimer(self, name)

    def record_latency(
        self, operation: str, duration_ms: float, metadata: dict | None = None
    ) -> None:
        record = LatencyRecord(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        if operation not in self._records:
            self._records[operation] = deque(maxlen=self.MAX_RECORDS_PER_OP)
        self._records[operation].append(record)

    def get_profile(self, operation: str) -> OperationProfile:
        records = self._records.get(operation)
        if not records:
            return OperationProfile(
                operation=operation,
                call_count=0,
                total_ms=0.0,
                avg_ms=0.0,
                min_ms=0.0,
                max_ms=0.0,
                p50_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                trend="stable",
                last_called=0.0,
            )
        return self._build_profile(operation, records)

    def get_all_profiles(self) -> list[OperationProfile]:
        return [
            self._build_profile(op, recs) for op, recs in self._records.items()
        ]

    def get_slow_operations(
        self, threshold_ms: float = 100.0
    ) -> list[OperationProfile]:
        return [
            p for p in self.get_all_profiles() if p.avg_ms >= threshold_ms
        ]

    def generate_report(self) -> LatencyReport:
        profiles = self.get_all_profiles()
        if not profiles:
            return LatencyReport(
                profiles=[],
                total_operations=0,
                slowest_operation="",
                avg_system_latency_ms=0.0,
                bottleneck_candidates=[],
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        slowest = max(profiles, key=lambda p: p.avg_ms)
        avg_latency = statistics.mean(p.avg_ms for p in profiles)
        bottleneck_threshold = avg_latency * 2.0
        bottlenecks = [
            p.operation for p in profiles if p.avg_ms > bottleneck_threshold
        ]

        return LatencyReport(
            profiles=sorted(profiles, key=lambda p: p.avg_ms, reverse=True),
            total_operations=len(profiles),
            slowest_operation=slowest.operation,
            avg_system_latency_ms=avg_latency,
            bottleneck_candidates=bottlenecks,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def reset(self) -> None:
        self._records.clear()

    def _build_profile(
        self, operation: str, records: deque[LatencyRecord]
    ) -> OperationProfile:
        durations = [r.duration_ms for r in records]
        sorted_d = sorted(durations)
        n = len(sorted_d)

        return OperationProfile(
            operation=operation,
            call_count=n,
            total_ms=sum(durations),
            avg_ms=statistics.mean(durations),
            min_ms=sorted_d[0],
            max_ms=sorted_d[-1],
            p50_ms=self._percentile(sorted_d, 50),
            p95_ms=self._percentile(sorted_d, 95),
            p99_ms=self._percentile(sorted_d, 99),
            trend=self._detect_trend(sorted_d),
            last_called=records[-1].timestamp,
        )

    @staticmethod
    def _percentile(sorted_values: list[float], pct: int) -> float:
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]
        idx = (pct / 100.0) * (n - 1)
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac

    @staticmethod
    def _detect_trend(sorted_by_time: list[float]) -> str:
        n = len(sorted_by_time)
        if n < 10:
            return "stable"
        window = max(1, n // 10)
        early_avg = statistics.mean(sorted_by_time[:window])
        late_avg = statistics.mean(sorted_by_time[-window:])
        if early_avg == 0:
            return "stable"
        change = (late_avg - early_avg) / early_avg
        if change > 0.15:
            return "degrading"
        if change < -0.15:
            return "improving"
        return "stable"


_default_profiler = LatencyProfiler()


def profile(name: str | None = None) -> Callable:
    """Decorator that profiles function execution time."""

    def decorator(fn: Callable) -> Callable:
        op_name = name or f"{fn.__module__}.{fn.__qualname__}"

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with _default_profiler.profile_operation(op_name):
                return fn(*args, **kwargs)

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _default_profiler.profile_operation(op_name):
                return await fn(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return wrapper

    return decorator
