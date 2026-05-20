"""Consolidation store metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from attention.consolidation.attention_memory_store import AttentionMemoryStore


@dataclass
class ConsolidationMetrics:
    memory_count: int = 0
    fill_ratio: float = 0.0
    trace_coverage: float = 0.0
    targets_tracked: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_count": self.memory_count,
            "fill_ratio": round(self.fill_ratio, 4),
            "trace_coverage": round(self.trace_coverage, 4),
            "targets_tracked": self.targets_tracked,
        }


def collect_consolidation_metrics(store: AttentionMemoryStore) -> ConsolidationMetrics:
    snap = store.snapshot()
    hist = snap.get("history", {})
    return ConsolidationMetrics(
        memory_count=int(snap.get("memory_count", 0)),
        fill_ratio=float(snap.get("fill_ratio", 0.0)),
        trace_coverage=float(snap.get("trace_coverage", 0.0)),
        targets_tracked=int(hist.get("targets_tracked", 0)),
    )
