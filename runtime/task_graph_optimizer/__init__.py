"""
Adaptive Task Graph Optimization — Analyze, detect bottlenecks, and optimize
task execution graphs based on structural and historical performance data.

Subsystem: runtime/task_graph_optimizer
Phase: D (Ambient OS v0.3)

Modules:
    bottleneck_detector    — Detect bottlenecks in DAG execution
    latency_analyzer       — Analyze execution latency patterns
    dependency_compressor  — Find opportunities to simplify dependency chains
    redundancy_detector    — Detect redundant nodes in the DAG
    optimizer              — Unified optimizer combining all analyzers
"""

from runtime.task_graph_optimizer.bottleneck_detector import (
    BottleneckDetector,
    BottleneckInfo,
    BottleneckReport,
    BottleneckType,
)
from runtime.task_graph_optimizer.latency_analyzer import (
    LatencyAnalyzer,
    LatencyReport,
    NodeLatency,
)
from runtime.task_graph_optimizer.dependency_compressor import (
    DependencyCompressor,
    CompressionProposal,
)
from runtime.task_graph_optimizer.redundancy_detector import (
    RedundancyDetector,
    RedundancyReport,
)
from runtime.task_graph_optimizer.optimizer import (
    TaskGraphOptimizer,
    OptimizationResult,
    BenchmarkResult,
)

__all__ = [
    "BottleneckDetector",
    "BottleneckInfo",
    "BottleneckReport",
    "BottleneckType",
    "LatencyAnalyzer",
    "LatencyReport",
    "NodeLatency",
    "DependencyCompressor",
    "CompressionProposal",
    "RedundancyDetector",
    "RedundancyReport",
    "TaskGraphOptimizer",
    "OptimizationResult",
    "BenchmarkResult",
]
