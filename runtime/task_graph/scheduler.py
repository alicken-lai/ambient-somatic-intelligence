"""
Task Graph Scheduler — Dependency resolution and parallel dispatch.

The Scheduler takes a TaskGraph and produces an execution plan:
  1. Validate the graph (no cycles, no orphans)
  2. Compute parallel stages via topological sort
  3. Dispatch ready tasks for execution
  4. Handle completion callbacks and unlock dependents
  5. Manage blocking conditions and timeouts

Execution modes:
  - sequential: one task at a time in topological order
  - parallel:   all independent tasks in a stage run concurrently
  - adaptive:   adjust parallelism based on system load
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus, RetryPolicy


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


class SchedulerEvent(str, Enum):
    TASK_READY = "task_ready"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    STAGE_COMPLETED = "stage_completed"
    GRAPH_COMPLETED = "graph_completed"
    GRAPH_FAILED = "graph_failed"


@dataclass
class SchedulerConfig:
    mode: ExecutionMode = ExecutionMode.PARALLEL
    max_concurrent: int = 5
    stage_timeout_seconds: float = 300.0
    task_timeout_seconds: float = 120.0
    fail_fast: bool = True  # Cancel remaining tasks on first failure


@dataclass
class ExecutionPlan:
    """A computed execution plan from the graph."""
    graph_id: str
    graph_name: str
    stages: list[list[str]]
    total_tasks: int
    max_parallelism: int
    estimated_stages: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "graph_name": self.graph_name,
            "stages": self.stages,
            "total_tasks": self.total_tasks,
            "max_parallelism": self.max_parallelism,
            "estimated_stages": self.estimated_stages,
        }


@dataclass
class ExecutionResult:
    """Result of a full graph execution."""
    graph_id: str
    success: bool
    total_tasks: int
    completed: int
    failed: int
    skipped: int
    duration_ms: float
    events: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "success": self.success,
            "total_tasks": self.total_tasks,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_ms": round(self.duration_ms, 1),
            "events_count": len(self.events),
            "errors": self.errors,
        }


TaskHandler = Callable[[TaskNode], Awaitable[Any]]


class Scheduler:
    """
    Orchestrates task execution according to the graph's dependency structure.

    Usage:
        scheduler = Scheduler(config=SchedulerConfig(mode=ExecutionMode.PARALLEL))
        plan = scheduler.plan(graph)
        result = await scheduler.execute(graph, handler_registry)
    """

    _MAX_EVENTS = 10000

    def __init__(self, config: SchedulerConfig | None = None):
        self.config = config or SchedulerConfig()
        self.events: list[dict[str, Any]] = []
        self._listeners: list[Callable[[SchedulerEvent, dict], None]] = []

    def on_event(self, listener: Callable[[SchedulerEvent, dict], None]) -> None:
        """Register an event listener."""
        self._listeners.append(listener)

    def _emit(self, event: SchedulerEvent, data: dict[str, Any]) -> None:
        entry = {
            "event": event.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        self.events.append(entry)
        if len(self.events) > self._MAX_EVENTS:
            self.events = self.events[-self._MAX_EVENTS:]
        for listener in self._listeners:
            try:
                listener(event, entry)
            except Exception:
                pass

    def plan(self, graph: TaskGraph) -> ExecutionPlan:
        """Compute an execution plan without running it."""
        stages = graph.parallel_stages()
        max_parallelism = max(len(s) for s in stages) if stages else 0

        return ExecutionPlan(
            graph_id=graph.id,
            graph_name=graph.name,
            stages=stages,
            total_tasks=len(graph.nodes),
            max_parallelism=min(max_parallelism, self.config.max_concurrent),
            estimated_stages=len(stages),
        )

    async def execute(
        self,
        graph: TaskGraph,
        handlers: dict[str, TaskHandler],
        default_handler: TaskHandler | None = None,
    ) -> ExecutionResult:
        """
        Execute the task graph respecting dependencies.

        Args:
            graph: The TaskGraph to execute
            handlers: Map of handler_name → async function
            default_handler: Fallback handler for unregistered task types
        """
        start_time = time.monotonic()
        self.events.clear()

        stages = graph.parallel_stages()

        for stage_idx, stage_tasks in enumerate(stages):
            if graph.is_complete:
                break

            self._emit(SchedulerEvent.STAGE_COMPLETED, {
                "stage": stage_idx,
                "tasks": stage_tasks,
            })

            if self.config.mode == ExecutionMode.SEQUENTIAL:
                for task_id in stage_tasks:
                    await self._execute_task(graph, task_id, handlers, default_handler)
                    if self.config.fail_fast and graph.failed_tasks:
                        self._cancel_remaining(graph)
                        break
            else:
                semaphore = asyncio.Semaphore(self.config.max_concurrent)
                tasks = []
                for task_id in stage_tasks:
                    tasks.append(
                        self._execute_with_semaphore(
                            semaphore, graph, task_id, handlers, default_handler
                        )
                    )

                await asyncio.gather(*tasks, return_exceptions=True)

                if self.config.fail_fast and graph.failed_tasks:
                    self._cancel_remaining(graph)
                    break

        duration = (time.monotonic() - start_time) * 1000
        progress = graph.progress

        result = ExecutionResult(
            graph_id=graph.id,
            success=graph.is_successful,
            total_tasks=progress["total"],
            completed=progress["by_status"].get("completed", 0),
            failed=progress["by_status"].get("failed", 0),
            skipped=progress["by_status"].get("skipped", 0),
            duration_ms=duration,
            events=self.events,
            errors=[
                {"task_id": n.id, "error": n.error}
                for n in graph.failed_tasks
            ],
        )

        event = SchedulerEvent.GRAPH_COMPLETED if result.success else SchedulerEvent.GRAPH_FAILED
        self._emit(event, {"result": result.to_dict()})

        return result

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        graph: TaskGraph,
        task_id: str,
        handlers: dict[str, TaskHandler],
        default_handler: TaskHandler | None,
    ) -> None:
        async with semaphore:
            await self._execute_task(graph, task_id, handlers, default_handler)

    async def _execute_task(
        self,
        graph: TaskGraph,
        task_id: str,
        handlers: dict[str, TaskHandler],
        default_handler: TaskHandler | None,
    ) -> None:
        """Execute a single task with retry support."""
        node = graph.nodes[task_id]

        if node.status.is_terminal:
            return

        handler = handlers.get(node.handler) or default_handler
        if not handler:
            node.mark_failed(f"No handler registered for '{node.handler}'")
            self._emit(SchedulerEvent.TASK_FAILED, {"task_id": task_id, "error": node.error})
            return

        while True:
            node.mark_running()
            self._emit(SchedulerEvent.TASK_STARTED, {"task_id": task_id, "attempt": node.attempts})

            try:
                if self.config.task_timeout_seconds > 0:
                    result = await asyncio.wait_for(
                        handler(node),
                        timeout=self.config.task_timeout_seconds,
                    )
                else:
                    result = await handler(node)

                node.mark_completed(result)
                self._emit(SchedulerEvent.TASK_COMPLETED, {
                    "task_id": task_id,
                    "duration_ms": node.duration_ms,
                })
                return

            except asyncio.TimeoutError:
                error = f"Task timed out after {self.config.task_timeout_seconds}s"
                node.mark_failed(error)

            except Exception as exc:
                node.mark_failed(str(exc))

            if node.status == TaskStatus.PENDING:
                delay = node.retry_policy.delay_for_attempt(node.attempts - 1)
                self._emit(SchedulerEvent.TASK_RETRYING, {
                    "task_id": task_id,
                    "attempt": node.attempts,
                    "delay_seconds": delay,
                })
                await asyncio.sleep(delay)
            else:
                self._emit(SchedulerEvent.TASK_FAILED, {
                    "task_id": task_id,
                    "error": node.error,
                    "attempts": node.attempts,
                })
                return

    def _cancel_remaining(self, graph: TaskGraph) -> None:
        """Cancel all non-terminal tasks (fail-fast mode)."""
        for node in graph.nodes.values():
            if not node.status.is_terminal and node.status != TaskStatus.RUNNING:
                node.mark_skipped("Cancelled due to fail-fast policy")

    def execute_sync(
        self,
        graph: TaskGraph,
        handlers: dict[str, Callable[[TaskNode], Any]],
    ) -> ExecutionResult:
        """
        Synchronous execution (wraps async in event loop).

        Useful for simple scripts that don't need async.
        Wraps each sync handler into an async coroutine via _make_async_handler.
        """
        async_handlers: dict[str, TaskHandler] = {}
        for name, handler in handlers.items():
            if asyncio.iscoroutinefunction(handler):
                async_handlers[name] = handler
            else:
                async_handlers[name] = self._make_async_handler(handler)

        return asyncio.run(self.execute(graph, async_handlers))

    @staticmethod
    def _make_async_handler(sync_handler: Callable[[TaskNode], Any]) -> TaskHandler:
        async def wrapper(node: TaskNode) -> Any:
            return sync_handler(node)
        return wrapper
