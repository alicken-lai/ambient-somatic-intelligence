"""
Ambient OS — Replay Metrics Collector

Tracks per-phase execution metrics, data quality, coverage, and timing
for the Reality Replay Program. Designed to feed into the Reality Score
computation and produce audit-friendly JSON artifacts.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class PhaseExecutionMetric:
    """Execution metrics for a single replay phase."""

    phase_id: str
    phase_name: str
    status: str = "pending"  # pending | running | completed | failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    records_processed: int = 0
    records_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 3)
        return None

    @property
    def success_rate(self) -> Optional[float]:
        total = self.records_processed + self.records_skipped
        if total == 0:
            return None
        return round(self.records_processed / total, 4)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["duration_seconds"] = self.duration_seconds
        d["success_rate"] = self.success_rate
        return d


@dataclass
class DataQualityMetric:
    """Data quality assessment for replay input data."""

    source: str
    total_records: int
    valid_records: int
    invalid_records: int = 0
    missing_fields: dict[str, int] = field(default_factory=dict)
    temporal_gaps: list[dict[str, Any]] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)

    @property
    def completeness(self) -> float:
        if self.total_records == 0:
            return 0.0
        return round(self.valid_records / self.total_records, 4)

    @property
    def integrity_score(self) -> float:
        if self.total_records == 0:
            return 0.0
        penalty = min(
            0.5,
            (self.invalid_records / self.total_records) * 0.3
            + len(self.temporal_gaps) * 0.05
            + len(self.anomalies) * 0.02,
        )
        return round(max(0.0, 1.0 - penalty), 4)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["completeness"] = self.completeness
        d["integrity_score"] = self.integrity_score
        return d


@dataclass
class CoverageMetric:
    """Measures how much of the system's operational surface was replayed."""

    domain: str
    total_events: int
    replayed_events: int
    time_span_hours: float
    domains_covered: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    @property
    def event_coverage(self) -> float:
        if self.total_events == 0:
            return 0.0
        return round(self.replayed_events / self.total_events, 4)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_coverage"] = self.event_coverage
        return d


class ReplayMetricsCollector:
    """
    Aggregates all replay metrics across phases.

    Usage:
        collector = ReplayMetricsCollector()
        collector.start_phase("1C", "Instinct Emergence")
        # ... do work ...
        collector.complete_phase("1C", records_processed=387)
        report = collector.summary()
    """

    def __init__(self) -> None:
        self._phases: dict[str, PhaseExecutionMetric] = {}
        self._data_quality: list[DataQualityMetric] = []
        self._coverage: list[CoverageMetric] = []
        self._session_start: float = time.time()

    def start_phase(self, phase_id: str, phase_name: str) -> PhaseExecutionMetric:
        metric = PhaseExecutionMetric(
            phase_id=phase_id,
            phase_name=phase_name,
            status="running",
            start_time=time.time(),
        )
        self._phases[phase_id] = metric
        return metric

    def complete_phase(
        self,
        phase_id: str,
        records_processed: int = 0,
        records_skipped: int = 0,
        artifacts: Optional[list[str]] = None,
    ) -> PhaseExecutionMetric:
        metric = self._phases[phase_id]
        metric.status = "completed"
        metric.end_time = time.time()
        metric.records_processed = records_processed
        metric.records_skipped = records_skipped
        if artifacts:
            metric.output_artifacts = artifacts
        return metric

    def fail_phase(self, phase_id: str, error: str) -> PhaseExecutionMetric:
        metric = self._phases[phase_id]
        metric.status = "failed"
        metric.end_time = time.time()
        metric.errors.append(error)
        return metric

    def add_phase_warning(self, phase_id: str, warning: str) -> None:
        self._phases[phase_id].warnings.append(warning)

    def add_data_quality(self, metric: DataQualityMetric) -> None:
        self._data_quality.append(metric)

    def add_coverage(self, metric: CoverageMetric) -> None:
        self._coverage.append(metric)

    def record_precomputed_phase(
        self,
        phase_id: str,
        phase_name: str,
        records_processed: int,
        records_skipped: int = 0,
        artifacts: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ) -> PhaseExecutionMetric:
        """Record a phase that was already executed (for retroactive tracking)."""
        metric = PhaseExecutionMetric(
            phase_id=phase_id,
            phase_name=phase_name,
            status="completed",
            records_processed=records_processed,
            records_skipped=records_skipped,
            output_artifacts=artifacts or [],
            warnings=warnings or [],
        )
        self._phases[phase_id] = metric
        return metric

    @property
    def total_duration_seconds(self) -> float:
        return round(time.time() - self._session_start, 3)

    @property
    def phases_completed(self) -> int:
        return sum(1 for p in self._phases.values() if p.status == "completed")

    @property
    def phases_failed(self) -> int:
        return sum(1 for p in self._phases.values() if p.status == "failed")

    @property
    def total_records_processed(self) -> int:
        return sum(p.records_processed for p in self._phases.values())

    @property
    def average_data_quality(self) -> float:
        if not self._data_quality:
            return 0.0
        return round(
            sum(dq.integrity_score for dq in self._data_quality) / len(self._data_quality),
            4,
        )

    def summary(self) -> dict[str, Any]:
        return {
            "session": {
                "total_duration_seconds": self.total_duration_seconds,
                "phases_total": len(self._phases),
                "phases_completed": self.phases_completed,
                "phases_failed": self.phases_failed,
                "total_records_processed": self.total_records_processed,
            },
            "phases": {pid: p.to_dict() for pid, p in self._phases.items()},
            "data_quality": {
                "sources": [dq.to_dict() for dq in self._data_quality],
                "average_integrity": self.average_data_quality,
            },
            "coverage": [c.to_dict() for c in self._coverage],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.summary(), indent=indent)
