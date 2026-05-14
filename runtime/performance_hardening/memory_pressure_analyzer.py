"""Analyze memory pressure from system components and identify optimization targets."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProcessMemoryStats:
    rss_mb: float
    vms_mb: float
    available: bool


@dataclass
class DataFileStats:
    path: str
    size_bytes: int
    size_human: str
    line_count: int
    file_type: str
    growth_risk: str


@dataclass
class CollectionStats:
    component: str
    collection_name: str
    max_size: int
    estimated_entry_bytes: int
    total_bytes_estimate: int
    is_bounded: bool


@dataclass
class RecallScanCost:
    total_records: int
    total_bytes: int
    estimated_scan_ms: float
    largest_layer: str
    largest_layer_records: int
    optimization_potential: str


@dataclass
class OptimizationTarget:
    target: str
    current_cost: str
    optimization: str
    expected_improvement: str
    priority: str
    effort: str


@dataclass
class MemoryPressureReport:
    process_memory: ProcessMemoryStats
    data_files: list[DataFileStats]
    collections: list[CollectionStats]
    recall_scan_cost: RecallScanCost
    optimization_targets: list[OptimizationTarget]
    total_data_on_disk_mb: float
    pressure_level: str
    generated_at: str


KNOWN_BOUNDED_COLLECTIONS: list[tuple[str, str, int, int]] = [
    ("SomaticSignalBus", "_history", 200, 512),
    ("IntegrationBus", "event_log", 500, 1024),
    ("MetricsCollector", "_histograms", 1000, 256),
    ("ExecutionTracer", "_completed_traces", 50, 2048),
    ("AgentTelemetry", "_completed_tasks", 200, 1024),
    ("AgentDecisionLog", "_events", 500, 512),
    ("CognitionTracer", "_traces", 1000, 768),
    ("MemoryFlowTracer", "_recalls", 2000, 512),
    ("Scheduler", "events", 10000, 256),
    ("FailurePropagator", "history", 1000, 512),
    ("RateTracker", "_samples", 500, 128),
    ("SignalCorrelator", "_pairs", 1000, 256),
    ("LoopDetector", "_detected", 200, 384),
    ("StabilityMonitor", "_snapshots", 500, 512),
    ("EntropyScorer", "_scores", 1000, 128),
]


class MemoryPressureAnalyzer:
    def __init__(self, root_dir: Path) -> None:
        self._root = root_dir

    def analyze(self) -> MemoryPressureReport:
        process_mem = self._analyze_process_memory()
        data_files = self._analyze_data_files()
        collections = self._analyze_in_memory_collections()
        recall_cost = self._analyze_recall_scan_cost()
        targets = self._identify_optimization_targets(
            data_files, collections, recall_cost
        )

        total_disk_bytes = sum(f.size_bytes for f in data_files)
        total_disk_mb = total_disk_bytes / (1024 * 1024)

        total_mem_estimate = sum(c.total_bytes_estimate for c in collections)
        pressure = self._classify_pressure(total_disk_mb, total_mem_estimate)

        return MemoryPressureReport(
            process_memory=process_mem,
            data_files=data_files,
            collections=collections,
            recall_scan_cost=recall_cost,
            optimization_targets=targets,
            total_data_on_disk_mb=round(total_disk_mb, 2),
            pressure_level=pressure,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _analyze_process_memory(self) -> ProcessMemoryStats:
        try:
            import resource

            rusage = resource.getrusage(resource.RUSAGE_SELF)
            rss_mb = rusage.ru_maxrss / (1024 * 1024)
            if os.uname().sysname == "Darwin":
                rss_mb = rusage.ru_maxrss / (1024 * 1024)
            else:
                rss_mb = rusage.ru_maxrss / 1024
            return ProcessMemoryStats(rss_mb=round(rss_mb, 2), vms_mb=0.0, available=True)
        except Exception:
            pass

        try:
            import psutil  # type: ignore[import-untyped]

            proc = psutil.Process()
            mem = proc.memory_info()
            return ProcessMemoryStats(
                rss_mb=round(mem.rss / (1024 * 1024), 2),
                vms_mb=round(mem.vms / (1024 * 1024), 2),
                available=True,
            )
        except Exception:
            return ProcessMemoryStats(rss_mb=0.0, vms_mb=0.0, available=False)

    def _analyze_data_files(self) -> list[DataFileStats]:
        results: list[DataFileStats] = []
        for ext in ("*.jsonl", "*.json"):
            for path in self._root.rglob(ext):
                rel = str(path.relative_to(self._root))
                if any(
                    skip in rel
                    for skip in (".git", "node_modules", "__pycache__", ".venv")
                ):
                    continue
                try:
                    size = os.path.getsize(path)
                    line_count = self._count_lines(path)
                    file_type = "jsonl" if path.suffix == ".jsonl" else "json"
                    growth_risk = self._assess_growth_risk(size, line_count, file_type)
                    results.append(
                        DataFileStats(
                            path=rel,
                            size_bytes=size,
                            size_human=self._humanize_bytes(size),
                            line_count=line_count,
                            file_type=file_type,
                            growth_risk=growth_risk,
                        )
                    )
                except OSError:
                    continue
        return sorted(results, key=lambda f: f.size_bytes, reverse=True)

    def _analyze_in_memory_collections(self) -> list[CollectionStats]:
        return [
            CollectionStats(
                component=comp,
                collection_name=name,
                max_size=max_sz,
                estimated_entry_bytes=entry_bytes,
                total_bytes_estimate=max_sz * entry_bytes,
                is_bounded=True,
            )
            for comp, name, max_sz, entry_bytes in KNOWN_BOUNDED_COLLECTIONS
        ]

    def _analyze_recall_scan_cost(self) -> RecallScanCost:
        memory_dir = self._root / "memory"
        layers = {
            "episodic": memory_dir / "episodic" / "records.jsonl",
            "dmn": memory_dir / "dmn.jsonl",
            "semantic": memory_dir / "semantic" / "entries.jsonl",
            "procedural": memory_dir / "procedural" / "entries.jsonl",
        }

        total_records = 0
        total_bytes = 0
        largest_layer = ""
        largest_count = 0

        for layer_name, path in layers.items():
            if path.exists():
                try:
                    size = os.path.getsize(path)
                    count = self._count_lines(path)
                    total_records += count
                    total_bytes += size
                    if count > largest_count:
                        largest_count = count
                        largest_layer = layer_name
                except OSError:
                    continue

        estimated_ms = total_records * 0.05

        if total_records > 5000:
            potential = "high — index or cache would dramatically reduce scan time"
        elif total_records > 1000:
            potential = "medium — cache layer would help for repeated queries"
        else:
            potential = "low — current scan cost is acceptable"

        return RecallScanCost(
            total_records=total_records,
            total_bytes=total_bytes,
            estimated_scan_ms=round(estimated_ms, 1),
            largest_layer=largest_layer,
            largest_layer_records=largest_count,
            optimization_potential=potential,
        )

    def _identify_optimization_targets(
        self,
        data_files: list[DataFileStats],
        collections: list[CollectionStats],
        recall_cost: RecallScanCost,
    ) -> list[OptimizationTarget]:
        targets: list[OptimizationTarget] = []

        if recall_cost.total_records > 500:
            targets.append(
                OptimizationTarget(
                    target="MemoryKernel.recall() full scan",
                    current_cost=f"{recall_cost.total_records} records, ~{recall_cost.estimated_scan_ms:.0f}ms per call",
                    optimization="Add RecallCache with TTL-based invalidation",
                    expected_improvement="90%+ reduction for repeated queries",
                    priority="high",
                    effort="low",
                )
            )

        large_files = [f for f in data_files if f.size_bytes > 500_000]
        for lf in large_files:
            targets.append(
                OptimizationTarget(
                    target=f"Large data file: {lf.path}",
                    current_cost=f"{lf.size_human}, {lf.line_count} lines",
                    optimization="Implement rotation or archival for old entries",
                    expected_improvement="Reduced scan surface and disk usage",
                    priority="medium",
                    effort="medium",
                )
            )

        high_growth = [f for f in data_files if f.growth_risk == "high"]
        for hg in high_growth:
            targets.append(
                OptimizationTarget(
                    target=f"High-growth file: {hg.path}",
                    current_cost=f"{hg.size_human}, growth_risk=high",
                    optimization="Add size cap or rotation policy",
                    expected_improvement="Bounded disk usage over time",
                    priority="medium",
                    effort="low",
                )
            )

        total_collection_bytes = sum(c.total_bytes_estimate for c in collections)
        if total_collection_bytes > 10 * 1024 * 1024:
            targets.append(
                OptimizationTarget(
                    target="In-memory bounded collections",
                    current_cost=f"~{total_collection_bytes / (1024 * 1024):.1f}MB across {len(collections)} collections",
                    optimization="Reduce max sizes for low-value collections",
                    expected_improvement="Lower baseline memory footprint",
                    priority="low",
                    effort="low",
                )
            )

        targets.append(
            OptimizationTarget(
                target="OCR blob scanning in episodic recall",
                current_cost="~3.3MB OCR data scanned on every recall",
                optimization="Exclude OCR content from default recall, add separate OCR search",
                expected_improvement="~50% reduction in episodic scan time",
                priority="high",
                effort="medium",
            )
        )

        return targets

    @staticmethod
    def _classify_pressure(disk_mb: float, mem_estimate: int) -> str:
        mem_mb = mem_estimate / (1024 * 1024)
        combined = disk_mb + mem_mb
        if combined > 500:
            return "critical"
        if combined > 100:
            return "high"
        if combined > 20:
            return "moderate"
        return "low"

    @staticmethod
    def _count_lines(path: Path) -> int:
        count = 0
        try:
            with open(path, "rb") as f:
                for _ in f:
                    count += 1
        except OSError:
            pass
        return count

    @staticmethod
    def _humanize_bytes(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f}{unit}" if unit != "B" else f"{size}B"
            size //= 1024
        return f"{size:.1f}TB"

    @staticmethod
    def _assess_growth_risk(size: int, line_count: int, file_type: str) -> str:
        if file_type == "jsonl" and line_count > 5000:
            return "high"
        if file_type == "jsonl" and line_count > 1000:
            return "medium"
        if size > 1_000_000:
            return "medium"
        if file_type == "jsonl" and line_count > 200:
            return "low"
        return "none"
