"""Area 6 — Sandboxed execution."""

from __future__ import annotations

from kernel.isolation.sandbox_context import SandboxContext
from kernel.isolation.write_target import WriteTarget


def test_sandbox_blocks_production_memory() -> None:
    sb = SandboxContext()
    with sb.activate("test-sandbox") as ctx:
        assert ctx.metadata.get("sandbox") is True
        assert sb.block_production_write(WriteTarget.MEMORY.value, context=ctx)
        assert not sb.block_production_write(WriteTarget.STATE.value, context=ctx)


def test_sandbox_memory_isolated() -> None:
    sb = SandboxContext()
    sb.memory.write("k", {"v": 1})
    assert sb.memory.read("k") == {"v": 1}
    sb.memory.clear()
    assert sb.memory.read("k") is None
