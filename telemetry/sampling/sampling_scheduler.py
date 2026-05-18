"""
Sampling Scheduler — Orchestrates telemetry sampling at configurable cadences.

Default maximum interval: 300 seconds (5 minutes).
Every registered source must declare its cadence and policies.

The scheduler is designed to be deterministic for replay purposes:
when given a fixed ``clock_fn``, the scheduling order and timing are
fully reproducible.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from telemetry.sampling.sampling_policy import SamplingPolicy

logger = logging.getLogger(__name__)

SampleFn = Callable[[], dict[str, Any]]


@dataclass
class SamplingStats:
    """Lifetime statistics for a single sampling source."""
    samples_taken: int = 0
    samples_missed: int = 0
    samples_failed: int = 0
    retries_total: int = 0
    consecutive_failures: int = 0
    last_sample_at: Optional[float] = None
    last_failure_at: Optional[float] = None
    last_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "samples_taken": self.samples_taken,
            "samples_missed": self.samples_missed,
            "samples_failed": self.samples_failed,
            "retries_total": self.retries_total,
            "consecutive_failures": self.consecutive_failures,
            "last_sample_at": (
                datetime.fromtimestamp(self.last_sample_at, tz=timezone.utc).isoformat()
                if self.last_sample_at else None
            ),
            "last_failure_at": (
                datetime.fromtimestamp(self.last_failure_at, tz=timezone.utc).isoformat()
                if self.last_failure_at else None
            ),
            "last_error": self.last_error,
        }


@dataclass
class _RegisteredSource:
    """Internal bookkeeping for a registered sampling source."""
    policy: SamplingPolicy
    sample_fn: SampleFn
    stats: SamplingStats = field(default_factory=SamplingStats)
    next_due_at: float = 0.0
    enabled: bool = True


class SamplingScheduler:
    """Orchestrates all telemetry sampling at configurable cadences.

    Default maximum interval: 300 seconds (5 minutes).
    Every registered source must declare its cadence and policies.

    Parameters
    ----------
    clock_fn:
        Callable returning current time as float (seconds since epoch).
        Defaults to ``time.time``.  Override for deterministic replay.
    on_escalation:
        Optional callback invoked when a source triggers failure escalation.
        Receives ``(source_name, escalation_level, stats_dict)``.
    tick_resolution_seconds:
        How often the scheduler loop checks for due sources.  Lower values
        give tighter timing but consume more CPU.
    """

    DEFAULT_MAX_CADENCE = 300

    def __init__(
        self,
        clock_fn: Callable[[], float] | None = None,
        on_escalation: Callable[[str, str, dict], None] | None = None,
        tick_resolution_seconds: float = 1.0,
    ):
        self._clock = clock_fn or time.time
        self._on_escalation = on_escalation
        self._tick_resolution = tick_resolution_seconds

        self._sources: dict[str, _RegisteredSource] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._rng = random.Random(42)
        self._sample_log: list[dict[str, Any]] = []
        self._max_sample_log = 5000

    # ── Registration ──────────────────────────────────────────────────

    def register(
        self,
        policy: SamplingPolicy,
        sample_fn: SampleFn,
        initial_due: float | None = None,
    ) -> None:
        """Register a telemetry source with its policy and collection function."""
        with self._lock:
            if policy.source_name in self._sources:
                raise ValueError(f"Source '{policy.source_name}' is already registered")
            now = initial_due if initial_due is not None else self._clock()
            jitter = self._compute_jitter(policy)
            self._sources[policy.source_name] = _RegisteredSource(
                policy=policy,
                sample_fn=sample_fn,
                next_due_at=now + jitter,
            )
            logger.info(
                "Registered source '%s' cadence=%ds priority=%s",
                policy.source_name,
                policy.desired_cadence_seconds,
                policy.priority,
            )

    def unregister(self, source_name: str) -> bool:
        """Remove a source from the scheduler.  Returns True if found."""
        with self._lock:
            return self._sources.pop(source_name, None) is not None

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background scheduling loop."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="SamplingScheduler", daemon=True
        )
        self._thread.start()
        logger.info("SamplingScheduler started")

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the scheduler to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None
        logger.info("SamplingScheduler stopped")

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── Manual trigger ────────────────────────────────────────────────

    def tick(self) -> list[dict[str, Any]]:
        """Run one scheduling tick manually (for testing / replay).

        Returns a list of sample results from sources that fired.
        """
        return self._execute_tick()

    def force_sample(self, source_name: str) -> dict[str, Any] | None:
        """Force an immediate sample from a specific source."""
        with self._lock:
            src = self._sources.get(source_name)
        if src is None:
            return None
        return self._collect_sample(src)

    # ── Query ─────────────────────────────────────────────────────────

    def get_stats(self, source_name: str) -> dict[str, Any] | None:
        src = self._sources.get(source_name)
        return src.stats.to_dict() if src else None

    def all_stats(self) -> dict[str, dict[str, Any]]:
        return {name: src.stats.to_dict() for name, src in self._sources.items()}

    def registered_sources(self) -> list[str]:
        return list(self._sources.keys())

    def summary(self) -> dict[str, Any]:
        total_taken = sum(s.stats.samples_taken for s in self._sources.values())
        total_missed = sum(s.stats.samples_missed for s in self._sources.values())
        total_failed = sum(s.stats.samples_failed for s in self._sources.values())
        return {
            "sources_registered": len(self._sources),
            "running": self.running,
            "total_samples_taken": total_taken,
            "total_samples_missed": total_missed,
            "total_samples_failed": total_failed,
            "sources": {
                name: {
                    "policy": src.policy.to_dict(),
                    "stats": src.stats.to_dict(),
                    "enabled": src.enabled,
                }
                for name, src in self._sources.items()
            },
        }

    def recent_samples(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self._sample_log[-limit:]))

    # ── Internal scheduling ───────────────────────────────────────────

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._execute_tick()
            except Exception:
                logger.exception("Unhandled error in sampling tick")
            self._stop_event.wait(timeout=self._tick_resolution)

    def _execute_tick(self) -> list[dict[str, Any]]:
        now = self._clock()
        due_sources: list[_RegisteredSource] = []

        with self._lock:
            for src in self._sources.values():
                if not src.enabled:
                    continue
                if now >= src.next_due_at:
                    due_sources.append(src)

        due_sources.sort(key=lambda s: _priority_rank(s.policy.priority))

        results: list[dict[str, Any]] = []
        for src in due_sources:
            gap = now - src.next_due_at
            if gap > src.policy.desired_cadence_seconds:
                src.stats.samples_missed += 1
                logger.warning(
                    "Missed sample window for '%s': gap=%.1fs cadence=%ds",
                    src.policy.source_name,
                    gap,
                    src.policy.desired_cadence_seconds,
                )

            result = self._collect_sample(src)
            if result is not None:
                results.append(result)

            jitter = self._compute_jitter(src.policy)
            src.next_due_at = self._clock() + src.policy.desired_cadence_seconds + jitter

        return results

    def _collect_sample(self, src: _RegisteredSource) -> dict[str, Any] | None:
        """Execute the sample function with retry logic."""
        last_error: str | None = None
        attempts = 1 + src.policy.retry_count

        for attempt in range(attempts):
            try:
                data = src.sample_fn()
                now = self._clock()
                record = {
                    "source": src.policy.source_name,
                    "timestamp": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
                    "attempt": attempt + 1,
                    "data": data,
                }
                src.stats.samples_taken += 1
                src.stats.consecutive_failures = 0
                src.stats.last_sample_at = now
                src.stats.last_error = None
                self._log_sample(record)
                return record

            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                src.stats.retries_total += 1
                logger.warning(
                    "Sample attempt %d/%d failed for '%s': %s",
                    attempt + 1,
                    attempts,
                    src.policy.source_name,
                    last_error,
                )
                if attempt < attempts - 1:
                    time.sleep(src.policy.retry_delay_seconds)

        src.stats.samples_failed += 1
        src.stats.consecutive_failures += 1
        src.stats.last_failure_at = self._clock()
        src.stats.last_error = last_error

        self._maybe_escalate(src)
        return None

    def _maybe_escalate(self, src: _RegisteredSource) -> None:
        if src.stats.consecutive_failures < src.policy.retry_count:
            return

        level = src.policy.failure_escalation
        logger.error(
            "Escalating failure for '%s': level=%s consecutive=%d",
            src.policy.source_name,
            level,
            src.stats.consecutive_failures,
        )
        if self._on_escalation:
            try:
                self._on_escalation(
                    src.policy.source_name,
                    level,
                    src.stats.to_dict(),
                )
            except Exception:
                logger.exception("Escalation callback failed for '%s'", src.policy.source_name)

    def _compute_jitter(self, policy: SamplingPolicy) -> float:
        if policy.allowed_jitter_seconds <= 0:
            return 0.0
        return self._rng.uniform(0, policy.allowed_jitter_seconds)

    def _log_sample(self, record: dict[str, Any]) -> None:
        self._sample_log.append(record)
        if len(self._sample_log) > self._max_sample_log:
            self._sample_log = self._sample_log[-self._max_sample_log:]


def _priority_rank(priority: str) -> int:
    return {"critical": 0, "standard": 1, "low": 2}.get(priority, 99)
