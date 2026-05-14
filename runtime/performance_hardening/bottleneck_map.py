"""Synthesize performance data into a bottleneck map with prioritized optimizations."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Bottleneck:
    id: str
    category: str
    component: str
    description: str
    impact: float
    feasibility: float
    current_metric: str
    target_metric: str
    priority_score: float


@dataclass
class OptimizationCandidate:
    bottleneck_id: str
    optimization: str
    expected_improvement: str
    effort: str
    risk: str
    files_affected: list[str]
    reversible: bool


@dataclass
class BottleneckMap:
    bottlenecks: list[Bottleneck]
    optimizations: list[OptimizationCandidate]
    total_bottlenecks: int
    critical_count: int
    top_priority: str | None
    estimated_overall_improvement: str
    generated_at: str


_KNOWN_BOTTLENECKS: list[dict[str, Any]] = [
    {
        "id": "recall_full_scan",
        "category": "algorithmic",
        "component": "MemoryKernel.recall()",
        "description": "Full sequential scan of every JSONL layer on every recall call. At 10K+ records this dominates latency.",
        "impact": 0.9,
        "feasibility": 0.8,
        "current_metric": "O(N) scan per recall, ~500ms at 10K records",
        "target_metric": "O(1) cache hit for repeated queries, <5ms",
        "optimization": "RecallCache with TTL-based invalidation + index-based lookup",
        "expected_improvement": "90%+ latency reduction for repeated queries",
        "effort": "low",
        "risk": "low",
        "files": ["memory/memory_kernel.py", "runtime/performance_hardening/recall_cache.py"],
        "reversible": True,
    },
    {
        "id": "synchronous_bus_dispatch",
        "category": "concurrency",
        "component": "SomaticSignalBus.emit()",
        "description": "Synchronous dispatch to all handlers blocks on each handler. 4+ on_any handlers fire on every signal.",
        "impact": 0.6,
        "feasibility": 0.7,
        "current_metric": "Blocking dispatch, ~20ms with 4 handlers",
        "target_metric": "Async dispatch, <2ms dispatch time",
        "optimization": "Add async dispatch option with fire-and-forget for non-critical handlers",
        "expected_improvement": "10x reduction in dispatch blocking time",
        "effort": "medium",
        "risk": "medium",
        "files": ["somatic/__init__.py", "somatic/signal_bus.py"],
        "reversible": True,
    },
    {
        "id": "duplicate_scoring_engines",
        "category": "algorithmic",
        "component": "SemanticRetriever + MemoryKernel",
        "description": "SemanticRetriever and MemoryKernel both implement independent scoring logic over the same data.",
        "impact": 0.6,
        "feasibility": 0.6,
        "current_metric": "Double CPU for same data, ~2x recall latency",
        "target_metric": "Single scoring engine via KernelRetriever",
        "optimization": "Consolidate scoring into KernelRetriever, deprecate SemanticRetriever direct scoring",
        "expected_improvement": "50% CPU reduction for recall operations",
        "effort": "medium",
        "risk": "low",
        "files": ["context/kernel_retriever.py", "context/semantic_retriever.py"],
        "reversible": True,
    },
    {
        "id": "sequential_parallel_dispatch",
        "category": "concurrency",
        "component": "AgentOrchestrator.dispatch_parallel()",
        "description": "dispatch_parallel is implemented as a sequential loop despite the name.",
        "impact": 0.5,
        "feasibility": 0.9,
        "current_metric": "Sequential execution, total_time = sum(all_tasks)",
        "target_metric": "Concurrent execution with asyncio.gather, total_time = max(all_tasks)",
        "optimization": "Replace sequential loop with asyncio.gather()",
        "expected_improvement": "Proportional to number of parallel tasks (2-4x typical)",
        "effort": "low",
        "risk": "low",
        "files": ["agents/base.py"],
        "reversible": True,
    },
    {
        "id": "eager_kernel_init",
        "category": "latency",
        "component": "AmbientKernel.__init__()",
        "description": "30+ imports and subsystem initializations performed eagerly on kernel startup.",
        "impact": 0.5,
        "feasibility": 0.7,
        "current_metric": "~500ms+ cold start with all subsystems",
        "target_metric": "<100ms cold start with lazy subsystem init",
        "optimization": "Lazy subsystem initialization — only init subsystems on first access",
        "expected_improvement": "5x faster kernel cold start",
        "effort": "medium",
        "risk": "low",
        "files": ["kernel.py"],
        "reversible": True,
    },
    {
        "id": "ocr_blob_scanning",
        "category": "io",
        "component": "Episodic memory recall",
        "description": "328 episodic records with OCR blobs (~10KB each) = ~3.3MB scanned on every recall.",
        "impact": 0.5,
        "feasibility": 0.8,
        "current_metric": "~3.3MB OCR data read per recall cycle",
        "target_metric": "OCR excluded from default recall, dedicated OCR search API",
        "optimization": "OCR content cleanup + exclusion from default recall path",
        "expected_improvement": "~50% reduction in episodic scan I/O",
        "effort": "medium",
        "risk": "low",
        "files": ["memory/episodic/records.jsonl"],
        "reversible": True,
    },
    {
        "id": "context_assembly_no_cache",
        "category": "latency",
        "component": "ContextAssembler.assemble()",
        "description": "Full retrieval + scoring + compression pipeline runs on every context assembly with no caching.",
        "impact": 0.4,
        "feasibility": 0.7,
        "current_metric": "Full pipeline per call, ~200ms typical",
        "target_metric": "Reuse cached blocks for sequential tasks, <50ms",
        "optimization": "ContextReuseOptimizer for block-level caching across sequential tasks",
        "expected_improvement": "60-80% reduction for sequential same-agent tasks",
        "effort": "low",
        "risk": "none",
        "files": ["context/__init__.py", "runtime/performance_hardening/context_reuse_optimizer.py"],
        "reversible": True,
    },
    {
        "id": "checkpoint_dir_creation",
        "category": "io",
        "component": "CheckpointManager.__init__()",
        "description": "Checkpoint creates directories on instantiation — side effect during init.",
        "impact": 0.2,
        "feasibility": 0.95,
        "current_metric": "Directory creation on every CheckpointManager init",
        "target_metric": "Lazy directory creation on first checkpoint write",
        "optimization": "Defer directory creation to first write operation",
        "expected_improvement": "Eliminates unnecessary I/O during init",
        "effort": "low",
        "risk": "none",
        "files": ["runtime/task_graph/checkpoint.py"],
        "reversible": True,
    },
]


class BottleneckMapper:
    def __init__(self, root_dir: Path) -> None:
        self._root = root_dir

    def generate(
        self,
        latency_report: Any = None,
        pressure_report: Any = None,
        cache_stats: Any = None,
        reuse_stats: Any = None,
    ) -> BottleneckMap:
        bottlenecks: list[Bottleneck] = []

        for spec in _KNOWN_BOTTLENECKS:
            bottlenecks.append(
                Bottleneck(
                    id=spec["id"],
                    category=spec["category"],
                    component=spec["component"],
                    description=spec["description"],
                    impact=spec["impact"],
                    feasibility=spec["feasibility"],
                    current_metric=spec["current_metric"],
                    target_metric=spec["target_metric"],
                    priority_score=spec["impact"] * spec["feasibility"],
                )
            )

        bottlenecks.extend(self._identify_latency_bottlenecks(latency_report))
        bottlenecks.extend(self._identify_memory_bottlenecks(pressure_report))
        bottlenecks.extend(self._identify_io_bottlenecks())
        bottlenecks.extend(self._identify_concurrency_bottlenecks())

        seen_ids: set[str] = set()
        unique: list[Bottleneck] = []
        for b in bottlenecks:
            if b.id not in seen_ids:
                seen_ids.add(b.id)
                unique.append(b)
        bottlenecks = unique

        bottlenecks = self._prioritize(bottlenecks)
        optimizations = self._generate_optimization_plan(bottlenecks)

        critical = [b for b in bottlenecks if b.priority_score >= 0.6]
        top = bottlenecks[0].id if bottlenecks else None

        improvement_pct = sum(
            b.impact * b.feasibility * 100 for b in bottlenecks[:3]
        ) / 3
        estimated = f"~{improvement_pct:.0f}% improvement if top 3 bottlenecks addressed"

        return BottleneckMap(
            bottlenecks=bottlenecks,
            optimizations=optimizations,
            total_bottlenecks=len(bottlenecks),
            critical_count=len(critical),
            top_priority=top,
            estimated_overall_improvement=estimated,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _identify_latency_bottlenecks(
        self, latency_report: Any
    ) -> list[Bottleneck]:
        if latency_report is None:
            return []
        results: list[Bottleneck] = []
        try:
            for profile in getattr(latency_report, "bottleneck_candidates", []):
                results.append(
                    Bottleneck(
                        id=f"latency_{profile}",
                        category="latency",
                        component=profile,
                        description=f"Operation '{profile}' identified as latency bottleneck by profiler",
                        impact=0.5,
                        feasibility=0.5,
                        current_metric="Above 2x system average",
                        target_metric="At or below system average",
                        priority_score=0.25,
                    )
                )
        except Exception:
            logger.debug("Failed to extract latency bottlenecks", exc_info=True)
        return results

    def _identify_memory_bottlenecks(
        self, pressure_report: Any
    ) -> list[Bottleneck]:
        if pressure_report is None:
            return []
        results: list[Bottleneck] = []
        try:
            for target in getattr(pressure_report, "optimization_targets", []):
                bid = f"memory_{target.target.replace(' ', '_').replace('.', '_')[:40]}"
                results.append(
                    Bottleneck(
                        id=bid,
                        category="memory",
                        component=target.target,
                        description=target.optimization,
                        impact=0.4 if target.priority == "high" else 0.2,
                        feasibility=0.7,
                        current_metric=target.current_cost,
                        target_metric=target.expected_improvement,
                        priority_score=0.28 if target.priority == "high" else 0.14,
                    )
                )
        except Exception:
            logger.debug("Failed to extract memory bottlenecks", exc_info=True)
        return results

    def _identify_io_bottlenecks(self) -> list[Bottleneck]:
        results: list[Bottleneck] = []
        log_files = [
            self._root / "logs" / "actions.jsonl",
            self._root / "logs" / "checksums.jsonl",
            self._root / "memory" / "episodic" / "records.jsonl",
        ]
        for path in log_files:
            if path.exists():
                try:
                    size = path.stat().st_size
                    if size > 500_000:
                        rel = str(path.relative_to(self._root))
                        results.append(
                            Bottleneck(
                                id=f"io_large_file_{path.stem}",
                                category="io",
                                component=rel,
                                description=f"Large log file ({size / 1024:.0f}KB) causes slow reads",
                                impact=0.3,
                                feasibility=0.8,
                                current_metric=f"{size / 1024:.0f}KB on disk",
                                target_metric="Rotated files < 100KB active",
                                priority_score=0.24,
                            )
                        )
                except OSError:
                    continue
        return results

    def _identify_concurrency_bottlenecks(self) -> list[Bottleneck]:
        return []

    def _prioritize(self, bottlenecks: list[Bottleneck]) -> list[Bottleneck]:
        for b in bottlenecks:
            b.priority_score = b.impact * b.feasibility
        return sorted(bottlenecks, key=lambda b: b.priority_score, reverse=True)

    def _generate_optimization_plan(
        self, bottlenecks: list[Bottleneck]
    ) -> list[OptimizationCandidate]:
        candidates: list[OptimizationCandidate] = []
        known_map = {spec["id"]: spec for spec in _KNOWN_BOTTLENECKS}

        for b in bottlenecks:
            spec = known_map.get(b.id)
            if spec:
                candidates.append(
                    OptimizationCandidate(
                        bottleneck_id=b.id,
                        optimization=spec["optimization"],
                        expected_improvement=spec["expected_improvement"],
                        effort=spec["effort"],
                        risk=spec["risk"],
                        files_affected=spec["files"],
                        reversible=spec["reversible"],
                    )
                )
            else:
                candidates.append(
                    OptimizationCandidate(
                        bottleneck_id=b.id,
                        optimization=b.description,
                        expected_improvement=b.target_metric,
                        effort="medium",
                        risk="low",
                        files_affected=[b.component],
                        reversible=True,
                    )
                )
        return candidates
