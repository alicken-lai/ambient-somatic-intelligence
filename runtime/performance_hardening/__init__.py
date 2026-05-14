"""Performance hardening infrastructure for Ambient OS."""
from __future__ import annotations

from runtime.performance_hardening.latency_profiler import (
    LatencyProfiler,
    LatencyRecord,
    LatencyReport,
    OperationProfile,
    OperationTimer,
    profile,
)
from runtime.performance_hardening.memory_pressure_analyzer import (
    CollectionStats,
    DataFileStats,
    MemoryPressureAnalyzer,
    MemoryPressureReport,
    OptimizationTarget,
    ProcessMemoryStats,
    RecallScanCost,
)
from runtime.performance_hardening.recall_cache import (
    CacheConfig,
    CacheEntry,
    CacheResult,
    CacheStats,
    RecallCache,
)
from runtime.performance_hardening.context_reuse_optimizer import (
    ContextReuseOptimizer,
    ReusableBlock,
    ReuseCheckResult,
    ReuseConfig,
    ReuseStats,
)
from runtime.performance_hardening.bottleneck_map import (
    Bottleneck,
    BottleneckMap,
    BottleneckMapper,
    OptimizationCandidate,
)

__all__ = [
    "LatencyProfiler",
    "LatencyRecord",
    "LatencyReport",
    "OperationProfile",
    "OperationTimer",
    "profile",
    "MemoryPressureAnalyzer",
    "CollectionStats",
    "DataFileStats",
    "MemoryPressureReport",
    "OptimizationTarget",
    "ProcessMemoryStats",
    "RecallScanCost",
    "RecallCache",
    "CacheConfig",
    "CacheEntry",
    "CacheResult",
    "CacheStats",
    "ContextReuseOptimizer",
    "ReusableBlock",
    "ReuseCheckResult",
    "ReuseConfig",
    "ReuseStats",
    "BottleneckMapper",
    "Bottleneck",
    "BottleneckMap",
    "OptimizationCandidate",
]
