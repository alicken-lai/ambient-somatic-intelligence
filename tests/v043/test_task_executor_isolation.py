"""Area 4 — Task executor isolation."""

from __future__ import annotations

import asyncio

import pytest

from runtime.task_graph.executor import TaskExecutor, _ISOLATION_AVAILABLE


def test_task_executor_binds_context() -> None:
    if not _ISOLATION_AVAILABLE:
        pytest.skip("isolation kernel not available")

    async def _run() -> None:
        executor = TaskExecutor(enable_guardian=False, enable_checkpoints=False)
        graph = executor.create_graph("iso-test")
        graph.add_task("t1", handler="noop")

        async def noop(node):
            return "ok"

        executor.register("noop", noop)
        result = await executor.run(graph)
        assert result.success
        assert executor.current_execution_context is None
        assert executor.current_graph() is None

    asyncio.run(_run())
