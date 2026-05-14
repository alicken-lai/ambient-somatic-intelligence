"""
Task Executor — High-level execution engine integrating DAG + Scheduler + Checkpoint.

The TaskExecutor is the main entry point for running task graphs:
  1. Build or receive a TaskGraph
  2. Plan execution via Scheduler
  3. Save checkpoint at each stage boundary
  4. Execute tasks with retry policies
  5. Report results and persist to memory

This module bridges the task_graph runtime with the rest of the Ambient OS:
  - Guardian integration for pre-execution validation
  - Memory integration for execution history
  - Context integration for task-aware budgeting
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus, RetryPolicy
from runtime.task_graph.scheduler import (
    Scheduler,
    SchedulerConfig,
    SchedulerEvent,
    ExecutionMode,
    ExecutionResult,
    TaskHandler,
)
from runtime.task_graph.checkpoint import CheckpointManager


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskExecutor:
    """
    High-level task execution engine.

    Usage:
        executor = TaskExecutor()

        # Define the workflow
        graph = executor.create_graph("deploy-feature")
        graph.add_task("migrate", handler="run_migration")
        graph.add_task("deploy", handler="deploy_service")
        graph.add_task("test", handler="run_tests")
        graph.add_edge("migrate", "deploy")
        graph.add_edge("deploy", "test")

        # Register handlers
        executor.register("run_migration", my_migration_fn)
        executor.register("deploy_service", my_deploy_fn)
        executor.register("run_tests", my_test_fn)

        # Execute
        result = await executor.run(graph)
    """

    def __init__(
        self,
        config: SchedulerConfig | None = None,
        enable_checkpoints: bool = True,
        enable_guardian: bool = True,
    ):
        self.config = config or SchedulerConfig()
        self.scheduler = Scheduler(config=self.config)
        self.checkpoint_mgr = CheckpointManager() if enable_checkpoints else None
        self.enable_guardian = enable_guardian
        self.handlers: dict[str, TaskHandler] = {}
        self.execution_log: list[dict[str, Any]] = []

    def register(self, handler_name: str, handler: Callable | TaskHandler) -> None:
        """Register a task handler function."""
        if asyncio.iscoroutinefunction(handler):
            self.handlers[handler_name] = handler
        else:
            self.handlers[handler_name] = self._wrap_sync(handler)

    def register_many(self, handlers: dict[str, Callable]) -> None:
        """Register multiple handlers at once."""
        for name, handler in handlers.items():
            self.register(name, handler)

    @staticmethod
    def _wrap_sync(fn: Callable) -> TaskHandler:
        async def wrapper(node: TaskNode) -> Any:
            return fn(node)
        return wrapper

    def create_graph(self, name: str) -> TaskGraph:
        """Create a new TaskGraph."""
        return TaskGraph(name=name)

    def plan(self, graph: TaskGraph) -> dict[str, Any]:
        """Get the execution plan without running."""
        plan = self.scheduler.plan(graph)
        return plan.to_dict()

    async def run(
        self,
        graph: TaskGraph,
        resume_from_checkpoint: bool = False,
    ) -> ExecutionResult:
        """
        Execute a TaskGraph.

        If resume_from_checkpoint is True and a checkpoint exists,
        resumes from the last saved state.
        """
        if resume_from_checkpoint and self.checkpoint_mgr:
            restored = self.checkpoint_mgr.restore(graph.id)
            if restored:
                graph = restored

        if self.enable_guardian:
            await self._guardian_validate(graph)

        if self.checkpoint_mgr and not getattr(self, "_checkpoint_listener_registered", False):
            self.scheduler.on_event(self._checkpoint_on_stage)
            self._checkpoint_listener_registered = True

        self._current_graph = graph
        try:
            result = await self.scheduler.execute(graph, self.handlers)

            self._log_execution(graph, result)

            if self.checkpoint_mgr:
                stages = graph.parallel_stages()
                self.checkpoint_mgr.save(graph, stage=len(stages), metadata={
                    "final": True,
                    "success": result.success,
                })

            return result
        finally:
            self._current_graph = None

    def run_sync(self, graph: TaskGraph) -> ExecutionResult:
        """Synchronous wrapper for run()."""
        return asyncio.run(self.run(graph))

    async def run_simple(
        self,
        tasks: list[dict[str, Any]],
        graph_name: str = "simple-workflow",
    ) -> ExecutionResult:
        """
        Convenience method: run a simple linear chain of tasks.

        Args:
            tasks: List of {"id": str, "handler": str, "params": dict}
            graph_name: Name for the graph
        """
        graph = self.create_graph(graph_name)

        prev_id = None
        for task_def in tasks:
            task_id = task_def["id"]
            graph.add_task(
                task_id=task_id,
                handler=task_def["handler"],
                name=task_def.get("name", task_id),
                params=task_def.get("params", {}),
            )
            if prev_id:
                graph.add_edge(prev_id, task_id)
            prev_id = task_id

        return await self.run(graph)

    async def run_parallel(
        self,
        tasks: list[dict[str, Any]],
        graph_name: str = "parallel-batch",
    ) -> ExecutionResult:
        """
        Convenience method: run all tasks in parallel (no dependencies).

        Args:
            tasks: List of {"id": str, "handler": str, "params": dict}
            graph_name: Name for the graph
        """
        graph = self.create_graph(graph_name)

        for task_def in tasks:
            graph.add_task(
                task_id=task_def["id"],
                handler=task_def["handler"],
                name=task_def.get("name", task_def["id"]),
                params=task_def.get("params", {}),
            )

        return await self.run(graph)

    async def _guardian_validate(self, graph: TaskGraph) -> None:
        """Pre-execution validation via Guardian (if available)."""
        try:
            scripts_path = str(Path(__file__).resolve().parent.parent.parent / "scripts")
            if scripts_path not in sys.path:
                sys.path.insert(0, scripts_path)
            from guardian_check import classify_action
            action_desc = f"Execute task graph '{graph.name}' with {len(graph.nodes)} tasks: {list(graph.nodes.keys())}"
            result = classify_action(action_desc, "task-graph-executor")

            if result.get("risk") == "BLOCK":
                raise PermissionError(
                    f"Guardian blocked task graph execution: {result.get('reason', 'unknown')}"
                )

            if result.get("risk") == "REVIEW_REQUIRED":
                self.execution_log.append({
                    "event": "guardian_review_required",
                    "graph": graph.name,
                    "timestamp": utc_now(),
                })

        except ImportError:
            pass

    def _checkpoint_on_stage(self, event: SchedulerEvent, data: dict[str, Any]) -> None:
        """Save checkpoint when a stage completes."""
        if event == SchedulerEvent.STAGE_COMPLETED and self.checkpoint_mgr:
            stage = data.get("stage", 0)
            if hasattr(self, "_current_graph"):
                self.checkpoint_mgr.save(self._current_graph, stage=stage)

    def _log_execution(self, graph: TaskGraph, result: ExecutionResult) -> None:
        """Log execution to internal log."""
        self.execution_log.append({
            "graph_id": graph.id,
            "graph_name": graph.name,
            "success": result.success,
            "total_tasks": result.total_tasks,
            "completed": result.completed,
            "failed": result.failed,
            "duration_ms": result.duration_ms,
            "timestamp": utc_now(),
        })

    def get_history(self) -> list[dict[str, Any]]:
        """Get execution history."""
        return list(self.execution_log)

    def status(self) -> dict[str, Any]:
        """Get executor status."""
        return {
            "registered_handlers": list(self.handlers.keys()),
            "executions": len(self.execution_log),
            "checkpoints_enabled": self.checkpoint_mgr is not None,
            "guardian_enabled": self.enable_guardian,
            "config": {
                "mode": self.config.mode.value,
                "max_concurrent": self.config.max_concurrent,
                "fail_fast": self.config.fail_fast,
                "task_timeout": self.config.task_timeout_seconds,
            },
        }


async def demo():
    """Demo execution of a task graph."""
    executor = TaskExecutor(
        config=SchedulerConfig(mode=ExecutionMode.PARALLEL, max_concurrent=3),
        enable_guardian=False,
    )

    async def mock_handler(node: TaskNode) -> str:
        await asyncio.sleep(0.1)
        return f"Completed: {node.name}"

    executor.register("build", mock_handler)
    executor.register("test", mock_handler)
    executor.register("deploy", mock_handler)

    graph = executor.create_graph("demo-pipeline")
    graph.add_task("lint", handler="build", params={"type": "lint"})
    graph.add_task("compile", handler="build", params={"type": "compile"})
    graph.add_task("unit_test", handler="test")
    graph.add_task("integration_test", handler="test")
    graph.add_task("deploy_staging", handler="deploy")

    graph.add_edge("lint", "unit_test")
    graph.add_edge("compile", "unit_test")
    graph.add_edge("compile", "integration_test")
    graph.add_edge("unit_test", "deploy_staging")
    graph.add_edge("integration_test", "deploy_staging")

    print("=== Execution Plan ===")
    print(json.dumps(executor.plan(graph), indent=2))
    print()

    print("=== Running ===")
    result = await executor.run(graph)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(demo())
