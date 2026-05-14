"""
Failure Propagation — Cascade failure signals through the task DAG.

When a task fails, all downstream dependents that cannot proceed must be
automatically marked as SKIPPED with a clear reason linking back to the
failed ancestor. This prevents wasted execution and provides a full
propagation chain for debugging.

Usage:
    propagator = FailurePropagator()
    chain = propagator.propagate(graph, failed_task_id="migrate")
    # All tasks downstream of "migrate" are now SKIPPED
    # chain contains the full propagation record
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus


@dataclass
class PropagationRecord:
    """A single propagation step: one task was skipped due to an ancestor failure."""
    task_id: str
    task_name: str
    failed_ancestor: str
    immediate_cause: str
    depth: int
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "failed_ancestor": self.failed_ancestor,
            "immediate_cause": self.immediate_cause,
            "depth": self.depth,
            "timestamp": self.timestamp,
        }


@dataclass
class PropagationChain:
    """Full record of a failure propagation event."""
    root_task_id: str
    root_error: str | None
    skipped_count: int
    records: list[PropagationRecord]
    duration_ms: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_task_id": self.root_task_id,
            "root_error": self.root_error,
            "skipped_count": self.skipped_count,
            "records": [r.to_dict() for r in self.records],
            "duration_ms": round(self.duration_ms, 3),
            "timestamp": self.timestamp,
        }

    @property
    def affected_task_ids(self) -> list[str]:
        return [r.task_id for r in self.records]


class FailurePropagator:
    """
    Traverses the DAG from a failed node and marks all reachable downstream
    dependents as SKIPPED, recording a chain for each propagation path.

    Supports both single-root and multi-root propagation. Tracks all
    propagation history for post-mortem debugging.
    """

    _MAX_HISTORY = 1000

    def __init__(self) -> None:
        self.history: list[PropagationChain] = []

    def propagate(
        self,
        graph: TaskGraph,
        failed_task_id: str,
    ) -> PropagationChain:
        """
        Propagate failure from a single root task through the DAG.

        Only tasks whose required dependencies (condition="success") point
        to a failed or skipped ancestor will be skipped. Tasks with
        condition="any" edges are NOT propagated through, since they can
        proceed regardless of upstream outcome.
        """
        start = time.monotonic()

        if failed_task_id not in graph.nodes:
            raise ValueError(f"Task '{failed_task_id}' not found in graph")

        root_node = graph.nodes[failed_task_id]
        root_error = root_node.error

        records: list[PropagationRecord] = []
        visited: set[str] = set()

        self._propagate_recursive(
            graph=graph,
            current_id=failed_task_id,
            root_id=failed_task_id,
            immediate_cause=failed_task_id,
            depth=0,
            visited=visited,
            records=records,
        )

        duration_ms = (time.monotonic() - start) * 1000
        chain = PropagationChain(
            root_task_id=failed_task_id,
            root_error=root_error,
            skipped_count=len(records),
            records=records,
            duration_ms=duration_ms,
        )

        self.history.append(chain)
        if len(self.history) > self._MAX_HISTORY:
            self.history = self.history[-self._MAX_HISTORY:]
        return chain

    def propagate_all_failures(
        self,
        graph: TaskGraph,
    ) -> list[PropagationChain]:
        """Propagate failures from ALL currently failed tasks in the graph."""
        chains: list[PropagationChain] = []
        for node in graph.nodes.values():
            if node.status == TaskStatus.FAILED:
                chain = self.propagate(graph, node.id)
                if chain.skipped_count > 0:
                    chains.append(chain)
        return chains

    def _propagate_recursive(
        self,
        graph: TaskGraph,
        current_id: str,
        root_id: str,
        immediate_cause: str,
        depth: int,
        visited: set[str],
        records: list[PropagationRecord],
    ) -> None:
        """BFS-like recursive traversal through dependents."""
        dependents = graph.get_dependents(current_id)

        for dep_id in dependents:
            if dep_id in visited:
                continue

            dep_node = graph.nodes[dep_id]

            if dep_node.status.is_terminal:
                continue

            dep_edges = [
                e for e in graph.edges
                if e.source == current_id and e.target == dep_id
            ]
            should_skip = any(e.condition == "success" for e in dep_edges)

            if not should_skip:
                continue

            visited.add(dep_id)

            reason = (
                f"Skipped: upstream task '{immediate_cause}' failed "
                f"(root cause: '{root_id}')"
            )
            dep_node.mark_skipped(reason)

            record = PropagationRecord(
                task_id=dep_id,
                task_name=dep_node.name,
                failed_ancestor=root_id,
                immediate_cause=immediate_cause,
                depth=depth + 1,
            )
            records.append(record)

            self._propagate_recursive(
                graph=graph,
                current_id=dep_id,
                root_id=root_id,
                immediate_cause=dep_id,
                depth=depth + 1,
                visited=visited,
                records=records,
            )

    def get_propagation_summary(self) -> dict[str, Any]:
        """Summary of all propagation events."""
        return {
            "total_propagations": len(self.history),
            "total_tasks_skipped": sum(c.skipped_count for c in self.history),
            "chains": [c.to_dict() for c in self.history],
        }

    def clear_history(self) -> None:
        self.history.clear()
