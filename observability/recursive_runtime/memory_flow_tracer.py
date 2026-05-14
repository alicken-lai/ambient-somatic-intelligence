"""
Memory Flow Tracer — Traces memory operations and data flow.

Captures the full lifecycle of memory interactions:
  - Recall operations (queries across memory layers)
  - Store operations (new records written)
  - Compression operations (data reduction events)
  - Memory pressure over time

Enables analysis of:
  - Recall frequency per layer and hit rates
  - Hot queries (most frequently recalled patterns)
  - Average latency of memory operations
  - Memory pressure timelines and compression effectiveness

Persists to: observability/memory_flow/flow_YYYY-MM-DD.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_FLOW_DIR = AMBIENT_ROOT / "observability" / "memory_flow"


@dataclass
class RecallEvent:
    """A memory recall operation."""
    query: str
    layer: str
    results_count: int
    duration_ms: float
    hit_rate: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "type": "recall",
            "query": self.query,
            "layer": self.layer,
            "results_count": self.results_count,
            "duration_ms": round(self.duration_ms, 2),
            "hit_rate": round(self.hit_rate, 4),
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class StoreEvent:
    """A memory store operation."""
    layer: str
    record_id: str
    tags: list[str]
    size: int
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "type": "store",
            "layer": self.layer,
            "record_id": self.record_id,
            "tags": self.tags,
            "size": self.size,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CompressionEvent:
    """A memory compression operation."""
    input_size: int
    output_size: int
    ratio: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "type": "compression",
            "input_size": self.input_size,
            "output_size": self.output_size,
            "ratio": round(self.ratio, 4),
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MemoryPressurePoint:
    """A memory pressure measurement at a point in time."""
    timestamp: float
    pressure_pct: float
    total_records: int
    layer_breakdown: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "pressure_pct": round(self.pressure_pct, 2),
            "total_records": self.total_records,
            "layer_breakdown": self.layer_breakdown,
        }


@dataclass
class MemoryFlowSummary:
    """Aggregated memory flow statistics."""
    total_recalls: int = 0
    total_stores: int = 0
    by_layer: dict[str, dict[str, Any]] = field(default_factory=dict)
    avg_latency_ms: float = 0.0
    hit_rate: float = 0.0
    hot_queries: list[dict[str, Any]] = field(default_factory=list)
    compression_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "total_recalls": self.total_recalls,
            "total_stores": self.total_stores,
            "by_layer": self.by_layer,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "hit_rate": round(self.hit_rate, 4),
            "hot_queries": self.hot_queries,
            "compression_ratio": round(self.compression_ratio, 4),
        }


class MemoryFlowTracer:
    """
    Traces memory operations and data flow throughout the system.

    Captures recalls, stores, and compressions with full timing
    and layer attribution. Enables analysis of memory access patterns,
    bottlenecks, and optimization opportunities.

    Usage:
        tracer = MemoryFlowTracer()

        tracer.trace_recall(
            query="recent user tasks",
            layer="episodic",
            results_count=5,
            duration=0.045,
            hit_rate=0.8,
        )

        tracer.trace_store(
            layer="working",
            record_id="rec_001",
            tags=["task", "frontend"],
            size=1024,
        )

        summary = tracer.get_flow_summary()
    """

    def __init__(self, persist: bool = True, max_events: int = 2000):
        self._recalls: list[RecallEvent] = []
        self._stores: list[StoreEvent] = []
        self._compressions: list[CompressionEvent] = []
        self._pressure_timeline: list[MemoryPressurePoint] = []
        self._query_frequency: dict[str, int] = defaultdict(int)
        self._max_events = max_events
        self._persist = persist

        if persist:
            MEMORY_FLOW_DIR.mkdir(parents=True, exist_ok=True)

    def trace_recall(
        self,
        query: str,
        layer: str,
        results_count: int,
        duration: float,
        hit_rate: float,
        metadata: dict[str, Any] | None = None,
    ) -> RecallEvent:
        """
        Log a memory recall operation.

        Args:
            query: The recall query
            layer: Memory layer queried (episodic, semantic, working, etc.)
            results_count: Number of results returned
            duration: Duration in seconds
            hit_rate: Fraction of results that were relevant (0.0 to 1.0)
            metadata: Additional context
        """
        event = RecallEvent(
            query=query,
            layer=layer,
            results_count=results_count,
            duration_ms=duration * 1000,
            hit_rate=max(0.0, min(1.0, hit_rate)),
            metadata=metadata or {},
        )

        self._recalls.append(event)
        if len(self._recalls) > self._max_events:
            self._recalls = self._recalls[-self._max_events:]

        self._query_frequency[query] += 1

        if self._persist:
            self._persist_event(event.to_dict())

        logger.debug("Memory recall: layer=%s results=%d %.1fms", layer, results_count, event.duration_ms)
        return event

    def trace_store(
        self,
        layer: str,
        record_id: str,
        tags: list[str] | None = None,
        size: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> StoreEvent:
        """
        Log a memory store operation.

        Args:
            layer: Target memory layer
            record_id: ID of the stored record
            tags: Tags associated with the record
            size: Size of the record in bytes
            metadata: Additional context
        """
        event = StoreEvent(
            layer=layer,
            record_id=record_id,
            tags=tags or [],
            size=size,
            metadata=metadata or {},
        )

        self._stores.append(event)
        if len(self._stores) > self._max_events:
            self._stores = self._stores[-self._max_events:]

        if self._persist:
            self._persist_event(event.to_dict())

        logger.debug("Memory store: layer=%s id=%s size=%d", layer, record_id, size)
        return event

    def trace_compression(
        self,
        input_size: int,
        output_size: int,
        ratio: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CompressionEvent:
        """
        Log a memory compression operation.

        Args:
            input_size: Size before compression
            output_size: Size after compression
            ratio: Compression ratio (computed if not provided)
            metadata: Additional context
        """
        if ratio is None:
            ratio = output_size / input_size if input_size > 0 else 1.0

        event = CompressionEvent(
            input_size=input_size,
            output_size=output_size,
            ratio=ratio,
            metadata=metadata or {},
        )

        self._compressions.append(event)
        if len(self._compressions) > self._max_events:
            self._compressions = self._compressions[-self._max_events:]

        if self._persist:
            self._persist_event(event.to_dict())

        logger.debug("Memory compression: %d → %d (%.2f ratio)", input_size, output_size, ratio)
        return event

    def record_pressure(
        self,
        pressure_pct: float,
        total_records: int,
        layer_breakdown: dict[str, int] | None = None,
    ) -> None:
        """Record a memory pressure measurement."""
        point = MemoryPressurePoint(
            timestamp=time.time(),
            pressure_pct=pressure_pct,
            total_records=total_records,
            layer_breakdown=layer_breakdown or {},
        )
        self._pressure_timeline.append(point)
        if len(self._pressure_timeline) > self._max_events:
            self._pressure_timeline = self._pressure_timeline[-self._max_events:]

    def get_flow_summary(self, time_range: tuple[float, float] | None = None) -> MemoryFlowSummary:
        """
        Get aggregated memory flow statistics.

        Args:
            time_range: Optional (start, end) filter as Unix timestamps

        Returns:
            MemoryFlowSummary with aggregate stats across all operations
        """
        recalls = self._recalls
        stores = self._stores
        compressions = self._compressions

        if time_range:
            start, end = time_range
            recalls = [r for r in recalls if start <= r.timestamp <= end]
            stores = [s for s in stores if start <= s.timestamp <= end]
            compressions = [c for c in compressions if start <= c.timestamp <= end]

        by_layer: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "recalls": 0, "stores": 0, "avg_latency_ms": 0.0, "hit_rate": 0.0
        })

        total_latency = 0.0
        total_hit_rate = 0.0
        layer_latencies: dict[str, list[float]] = defaultdict(list)
        layer_hit_rates: dict[str, list[float]] = defaultdict(list)

        for r in recalls:
            by_layer[r.layer]["recalls"] += 1
            total_latency += r.duration_ms
            total_hit_rate += r.hit_rate
            layer_latencies[r.layer].append(r.duration_ms)
            layer_hit_rates[r.layer].append(r.hit_rate)

        for s in stores:
            by_layer[s.layer]["stores"] += 1

        for layer, data in by_layer.items():
            latencies = layer_latencies.get(layer, [])
            hit_rates = layer_hit_rates.get(layer, [])
            data["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
            data["hit_rate"] = round(sum(hit_rates) / len(hit_rates), 4) if hit_rates else 0.0

        hot_queries = sorted(self._query_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

        avg_compression = 0.0
        if compressions:
            avg_compression = sum(c.ratio for c in compressions) / len(compressions)

        return MemoryFlowSummary(
            total_recalls=len(recalls),
            total_stores=len(stores),
            by_layer=dict(by_layer),
            avg_latency_ms=round(total_latency / len(recalls), 2) if recalls else 0.0,
            hit_rate=round(total_hit_rate / len(recalls), 4) if recalls else 0.0,
            hot_queries=[{"query": q, "count": c} for q, c in hot_queries],
            compression_ratio=round(avg_compression, 4),
        )

    def get_memory_pressure_timeline(self) -> list[dict[str, Any]]:
        """Get memory pressure measurements over time."""
        return [p.to_dict() for p in self._pressure_timeline]

    def _persist_event(self, event_dict: dict[str, Any]) -> None:
        """Append event to daily JSONL file."""
        try:
            date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            filepath = MEMORY_FLOW_DIR / f"flow_{date_str}.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist memory flow event")
