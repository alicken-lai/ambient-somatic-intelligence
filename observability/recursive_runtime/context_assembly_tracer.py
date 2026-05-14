"""
Context Assembly Tracer — Traces the context assembly process.

Monitors how context is assembled for each agent task:
  - Which sources contribute to the context window
  - Token budget allocation and utilization
  - Retrieval decisions and utility scoring
  - Waste detection (unused or low-utility context)

Enables optimization of context assembly by identifying:
  - Budget waste (tokens allocated but not useful)
  - Retrieval efficiency (are we finding the right information?)
  - Source ranking accuracy (do top sources actually help?)

Persists alongside other recursive runtime traces.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
CONTEXT_TRACES_DIR = AMBIENT_ROOT / "observability" / "cognition_traces"


@dataclass
class AssemblyEvent:
    """A context assembly operation."""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent_id: str = ""
    task_id: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0
    budget: int = 0
    selections: list[dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def budget_utilization(self) -> float:
        """Fraction of budget actually used."""
        return self.total_tokens / self.budget if self.budget > 0 else 0.0

    @property
    def waste_tokens(self) -> int:
        """Tokens allocated but unused."""
        return max(0, self.budget - self.total_tokens)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "type": "assembly",
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "sources": self.sources,
            "total_tokens": self.total_tokens,
            "budget": self.budget,
            "budget_utilization": round(self.budget_utilization, 4),
            "waste_tokens": self.waste_tokens,
            "selections": self.selections,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class RetrievalEvent:
    """A retrieval decision during context assembly."""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    query: str = ""
    results: list[dict[str, Any]] = field(default_factory=list)
    utility_scores: list[float] = field(default_factory=list)
    selected: list[int] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def retrieval_efficiency(self) -> float:
        """Fraction of results that were actually selected."""
        return len(self.selected) / len(self.results) if self.results else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "type": "retrieval",
            "event_id": self.event_id,
            "query": self.query,
            "results_count": len(self.results),
            "utility_scores": [round(s, 4) for s in self.utility_scores],
            "selected_count": len(self.selected),
            "retrieval_efficiency": round(self.retrieval_efficiency, 4),
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AssemblyReport:
    """Aggregated report on context assembly efficiency."""
    total_assemblies: int = 0
    avg_tokens: float = 0.0
    budget_utilization: float = 0.0
    retrieval_efficiency: float = 0.0
    waste_ratio: float = 0.0
    top_sources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "total_assemblies": self.total_assemblies,
            "avg_tokens": round(self.avg_tokens, 1),
            "budget_utilization": round(self.budget_utilization, 4),
            "retrieval_efficiency": round(self.retrieval_efficiency, 4),
            "waste_ratio": round(self.waste_ratio, 4),
            "top_sources": self.top_sources,
        }


class ContextAssemblyTracer:
    """
    Traces the context assembly process.

    Monitors how context windows are assembled, including source
    selection, token budget allocation, retrieval utility scoring,
    and waste detection.

    Usage:
        tracer = ContextAssemblyTracer()

        tracer.trace_assembly(
            agent_id="frontend-agent",
            task_id="task_001",
            sources=[{"name": "memory", "tokens": 500}, {"name": "rules", "tokens": 200}],
            total_tokens=700,
            budget=1000,
            selections=[{"source": "memory", "reason": "high relevance"}],
        )

        report = tracer.get_assembly_report()
    """

    def __init__(self, persist: bool = True, max_events: int = 1000):
        self._assemblies: list[AssemblyEvent] = []
        self._retrievals: list[RetrievalEvent] = []
        self._source_frequency: dict[str, int] = defaultdict(int)
        self._max_events = max_events
        self._persist = persist

        if persist:
            CONTEXT_TRACES_DIR.mkdir(parents=True, exist_ok=True)

    def trace_assembly(
        self,
        agent_id: str,
        task_id: str,
        sources: list[dict[str, Any]],
        total_tokens: int,
        budget: int,
        selections: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AssemblyEvent:
        """
        Log a context assembly operation.

        Args:
            agent_id: Agent performing the assembly
            task_id: Task the context is for
            sources: List of sources contributing to context
            total_tokens: Total tokens used in assembly
            budget: Token budget allocated
            selections: Which sources were selected and why
            metadata: Additional context
        """
        event = AssemblyEvent(
            agent_id=agent_id,
            task_id=task_id,
            sources=sources,
            total_tokens=total_tokens,
            budget=budget,
            selections=selections or [],
            metadata=metadata or {},
        )

        self._assemblies.append(event)
        if len(self._assemblies) > self._max_events:
            self._assemblies = self._assemblies[-self._max_events:]

        for source in sources:
            source_name = source.get("name", "unknown")
            self._source_frequency[source_name] += 1

        if self._persist:
            self._persist_event(event.to_dict())

        logger.debug(
            "Context assembly: agent=%s tokens=%d/%d (%.0f%% utilization)",
            agent_id, total_tokens, budget, event.budget_utilization * 100
        )
        return event

    def trace_retrieval(
        self,
        query: str,
        results: list[dict[str, Any]],
        utility_scores: list[float],
        selected: list[int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RetrievalEvent:
        """
        Log a retrieval decision during context assembly.

        Args:
            query: The retrieval query
            results: Retrieved results
            utility_scores: Utility scores for each result
            selected: Indices of results that were selected for context
            metadata: Additional context
        """
        event = RetrievalEvent(
            query=query,
            results=results,
            utility_scores=utility_scores,
            selected=selected or [],
            metadata=metadata or {},
        )

        self._retrievals.append(event)
        if len(self._retrievals) > self._max_events:
            self._retrievals = self._retrievals[-self._max_events:]

        if self._persist:
            self._persist_event(event.to_dict())

        logger.debug(
            "Context retrieval: query=%s results=%d selected=%d efficiency=%.2f",
            query[:50], len(results), len(event.selected), event.retrieval_efficiency
        )
        return event

    def get_assembly_report(self, time_range: tuple[float, float] | None = None) -> AssemblyReport:
        """
        Generate report on context assembly efficiency.

        Args:
            time_range: Optional (start, end) filter as Unix timestamps

        Returns:
            AssemblyReport with aggregate statistics
        """
        assemblies = self._assemblies
        retrievals = self._retrievals

        if time_range:
            start, end = time_range
            assemblies = [a for a in assemblies if start <= a.timestamp <= end]
            retrievals = [r for r in retrievals if start <= r.timestamp <= end]

        if not assemblies:
            return AssemblyReport()

        total_tokens = sum(a.total_tokens for a in assemblies)
        total_budget = sum(a.budget for a in assemblies)
        total_waste = sum(a.waste_tokens for a in assemblies)

        avg_retrieval_eff = 0.0
        if retrievals:
            avg_retrieval_eff = sum(r.retrieval_efficiency for r in retrievals) / len(retrievals)

        top_sources = sorted(
            self._source_frequency.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return AssemblyReport(
            total_assemblies=len(assemblies),
            avg_tokens=total_tokens / len(assemblies),
            budget_utilization=total_tokens / total_budget if total_budget > 0 else 0.0,
            retrieval_efficiency=avg_retrieval_eff,
            waste_ratio=total_waste / total_budget if total_budget > 0 else 0.0,
            top_sources=[{"source": s, "count": c} for s, c in top_sources],
        )

    def _persist_event(self, event_dict: dict[str, Any]) -> None:
        """Append event to daily JSONL file."""
        try:
            date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            filepath = CONTEXT_TRACES_DIR / f"context_assembly_{date_str}.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist context assembly event")
