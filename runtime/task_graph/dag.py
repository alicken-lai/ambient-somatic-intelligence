"""
Task Graph DAG — Core data structures for dependency-aware task execution.

A TaskGraph is a Directed Acyclic Graph where:
  - Nodes are tasks with state machines (pending → running → completed/failed/cancelled)
  - Edges define dependencies (task B depends on task A)
  - The graph enforces acyclicity and provides topological ordering

Example:
    graph = TaskGraph("deploy-feature")
    graph.add_task("schema", handler="migrate_db")
    graph.add_task("backend", handler="deploy_backend")
    graph.add_task("frontend", handler="deploy_frontend")
    graph.add_task("tests", handler="run_e2e")
    graph.add_edge("schema", "backend")     # backend depends on schema
    graph.add_edge("schema", "frontend")    # frontend depends on schema
    graph.add_edge("backend", "tests")      # tests depend on backend
    graph.add_edge("frontend", "tests")     # tests depend on frontend
    # Result: schema → (backend, frontend) in parallel → tests
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class TaskStatus(str, Enum):
    PENDING = "pending"
    BLOCKED = "blocked"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

    @property
    def is_terminal(self) -> bool:
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SKIPPED)

    @property
    def is_success(self) -> bool:
        return self == TaskStatus.COMPLETED


class RetryPolicy:
    """Configurable retry behavior for failed tasks."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_seconds: float = 2.0,
        backoff_multiplier: float = 2.0,
        retryable_errors: list[str] | None = None,
    ):
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.backoff_multiplier = backoff_multiplier
        self.retryable_errors = retryable_errors or []

    def should_retry(self, attempt: int, error: str) -> bool:
        if attempt >= self.max_retries:
            return False
        if self.retryable_errors:
            return any(e in error for e in self.retryable_errors)
        return True

    def delay_for_attempt(self, attempt: int) -> float:
        return self.backoff_seconds * (self.backoff_multiplier ** attempt)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "backoff_seconds": self.backoff_seconds,
            "backoff_multiplier": self.backoff_multiplier,
            "retryable_errors": self.retryable_errors,
        }


@dataclass
class TaskNode:
    """A single task in the graph."""
    id: str
    name: str
    handler: str
    status: TaskStatus = TaskStatus.PENDING
    params: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str | None = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    attempts: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if not self.started_at or not self.completed_at:
            return None
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at)
        return (end - start).total_seconds() * 1000

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.attempts += 1

    def mark_completed(self, result: Any = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error: str) -> None:
        self.error = error
        if self.retry_policy.should_retry(self.attempts, error):
            self.status = TaskStatus.PENDING
        else:
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_cancelled(self) -> None:
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_skipped(self, reason: str = "") -> None:
        self.status = TaskStatus.SKIPPED
        self.error = reason
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "handler": self.handler,
            "status": self.status.value,
            "params": self.params,
            "result": str(self.result)[:200] if self.result else None,
            "error": self.error,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "retry_policy": self.retry_policy.to_dict(),
        }


@dataclass
class TaskEdge:
    """A dependency edge: source must complete before target can start."""
    source: str  # task ID that must complete first
    target: str  # task ID that depends on source
    condition: str = "success"  # "success", "any", "failure"

    def is_satisfied(self, source_status: TaskStatus) -> bool:
        if self.condition == "success":
            return source_status == TaskStatus.COMPLETED
        elif self.condition == "any":
            return source_status.is_terminal
        elif self.condition == "failure":
            return source_status == TaskStatus.FAILED
        return False


class TaskGraph:
    """
    A Directed Acyclic Graph of tasks with dependency tracking.

    Usage:
        graph = TaskGraph("my-workflow")
        graph.add_task("step1", handler="do_thing_1")
        graph.add_task("step2", handler="do_thing_2")
        graph.add_edge("step1", "step2")  # step2 depends on step1
        ready = graph.get_ready_tasks()   # Returns ["step1"]
    """

    def __init__(self, name: str, graph_id: str | None = None):
        self.name = name
        self.id = graph_id or str(uuid.uuid4())[:8]
        self.nodes: dict[str, TaskNode] = {}
        self.edges: list[TaskEdge] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.metadata: dict[str, Any] = {}

    def add_task(
        self,
        task_id: str,
        handler: str,
        name: str | None = None,
        params: dict[str, Any] | None = None,
        retry_policy: RetryPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskNode:
        """Add a task node to the graph."""
        if task_id in self.nodes:
            raise ValueError(f"Task '{task_id}' already exists in graph")

        node = TaskNode(
            id=task_id,
            name=name or task_id,
            handler=handler,
            params=params or {},
            retry_policy=retry_policy or RetryPolicy(),
            metadata=metadata or {},
        )
        self.nodes[task_id] = node
        return node

    def add_edge(self, source: str, target: str, condition: str = "success") -> TaskEdge:
        """Add a dependency edge (source must complete before target)."""
        if source not in self.nodes:
            raise ValueError(f"Source task '{source}' not found in graph")
        if target not in self.nodes:
            raise ValueError(f"Target task '{target}' not found in graph")
        if source == target:
            raise ValueError("Self-dependency not allowed")

        edge = TaskEdge(source=source, target=target, condition=condition)
        self.edges.append(edge)

        if self._has_cycle():
            self.edges.remove(edge)
            raise ValueError(f"Adding edge {source}→{target} would create a cycle")

        return edge

    def get_dependencies(self, task_id: str) -> list[str]:
        """Get all tasks that must complete before this task."""
        return [e.source for e in self.edges if e.target == task_id]

    def get_dependents(self, task_id: str) -> list[str]:
        """Get all tasks that depend on this task."""
        return [e.target for e in self.edges if e.source == task_id]

    def get_ready_tasks(self) -> list[TaskNode]:
        """Get tasks whose dependencies are all satisfied and can be executed."""
        ready: list[TaskNode] = []

        for task_id, node in self.nodes.items():
            if node.status not in (TaskStatus.PENDING, TaskStatus.READY):
                continue

            deps = self.get_dependencies(task_id)
            if not deps:
                node.status = TaskStatus.READY
                ready.append(node)
                continue

            all_satisfied = True
            for dep_id in deps:
                dep_node = self.nodes[dep_id]
                dep_edges = [e for e in self.edges if e.source == dep_id and e.target == task_id]
                for edge in dep_edges:
                    if not edge.is_satisfied(dep_node.status):
                        all_satisfied = False
                        break
                if not all_satisfied:
                    break

            if all_satisfied:
                node.status = TaskStatus.READY
                ready.append(node)
            else:
                node.status = TaskStatus.BLOCKED

        return ready

    def topological_order(self) -> list[str]:
        """Return tasks in topological order (respecting dependencies)."""
        in_degree: dict[str, int] = {task_id: 0 for task_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            queue.sort()
            current = queue.pop(0)
            order.append(current)
            for edge in self.edges:
                if edge.source == current:
                    in_degree[edge.target] -= 1
                    if in_degree[edge.target] == 0:
                        queue.append(edge.target)

        if len(order) != len(self.nodes):
            raise RuntimeError("Graph contains a cycle (should not happen)")

        return order

    def parallel_stages(self) -> list[list[str]]:
        """
        Group tasks into parallel execution stages.

        Each stage contains tasks that can run simultaneously.
        Stages execute sequentially.
        """
        in_degree: dict[str, int] = {task_id: 0 for task_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] += 1

        stages: list[list[str]] = []
        remaining = set(self.nodes.keys())

        while remaining:
            stage = [tid for tid in remaining if in_degree[tid] == 0]
            if not stage:
                raise RuntimeError("Cycle detected in remaining tasks")

            stages.append(sorted(stage))
            for tid in stage:
                remaining.remove(tid)
                for edge in self.edges:
                    if edge.source == tid and edge.target in remaining:
                        in_degree[edge.target] -= 1

        return stages

    @property
    def is_complete(self) -> bool:
        """Check if all tasks have reached a terminal state."""
        return all(node.status.is_terminal for node in self.nodes.values())

    @property
    def is_successful(self) -> bool:
        """Check if all tasks completed successfully (or were skipped)."""
        return all(
            node.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for node in self.nodes.values()
        )

    @property
    def failed_tasks(self) -> list[TaskNode]:
        return [n for n in self.nodes.values() if n.status == TaskStatus.FAILED]

    @property
    def progress(self) -> dict[str, Any]:
        """Get execution progress summary."""
        by_status: dict[str, int] = {}
        for node in self.nodes.values():
            by_status[node.status.value] = by_status.get(node.status.value, 0) + 1

        total = len(self.nodes)
        done = sum(1 for n in self.nodes.values() if n.status.is_terminal)

        return {
            "total": total,
            "done": done,
            "progress_pct": round(done / total * 100, 1) if total else 0,
            "by_status": by_status,
            "is_complete": self.is_complete,
            "is_successful": self.is_successful,
        }

    def cancel_downstream(self, failed_task_id: str) -> list[str]:
        """Cancel all tasks downstream of a failed task."""
        cancelled: list[str] = []
        to_cancel = set(self.get_dependents(failed_task_id))

        while to_cancel:
            task_id = to_cancel.pop()
            node = self.nodes[task_id]
            if not node.status.is_terminal:
                node.mark_skipped(f"Upstream task '{failed_task_id}' failed")
                cancelled.append(task_id)
                to_cancel.update(self.get_dependents(task_id))

        return cancelled

    def _has_cycle(self) -> bool:
        """Check for cycles using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in self.nodes}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for edge in self.edges:
                if edge.source == node:
                    target = edge.target
                    if color[target] == GRAY:
                        return True
                    if color[target] == WHITE and dfs(target):
                        return True
            color[node] = BLACK
            return False

        return any(color[tid] == WHITE and dfs(tid) for tid in self.nodes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "nodes": {tid: n.to_dict() for tid, n in self.nodes.items()},
            "edges": [{"source": e.source, "target": e.target, "condition": e.condition} for e in self.edges],
            "stages": self.parallel_stages(),
            "progress": self.progress,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskGraph":
        """Reconstruct a TaskGraph from serialized dict."""
        graph = cls(name=data["name"], graph_id=data.get("id"))
        graph.created_at = data.get("created_at", graph.created_at)

        for tid, ndata in data.get("nodes", {}).items():
            node = graph.add_task(
                task_id=tid,
                handler=ndata["handler"],
                name=ndata.get("name", tid),
                params=ndata.get("params", {}),
            )
            node.status = TaskStatus(ndata.get("status", "pending"))
            node.result = ndata.get("result")
            node.error = ndata.get("error")
            node.attempts = ndata.get("attempts", 0)
            node.started_at = ndata.get("started_at")
            node.completed_at = ndata.get("completed_at")

        for edata in data.get("edges", []):
            graph.add_edge(edata["source"], edata["target"], edata.get("condition", "success"))

        return graph
