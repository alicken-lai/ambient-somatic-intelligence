"""Phase 3 — GovernedMemoryWriter."""

from __future__ import annotations

import json

from kernel.isolation.governed_memory_writer import GovernedMemoryWriter


def test_append_dmn_governed(governed_context, tmp_path):
    writer = GovernedMemoryWriter(memory_root=tmp_path / "memory")
    path = writer.append_dmn(
        {"content": "v044b", "tags": ["test"]},
        context=governed_context,
        mutation_reason="test",
    )
    assert path.exists()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lines[-1])["content"] == "v044b"
