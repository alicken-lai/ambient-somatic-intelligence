"""Phase 1 — GuardedFileWriter."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.execution_scope import ExecutionScope
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.root_resolver import RootResolver
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget


def test_append_jsonl_with_context(governed_context: ExecutionContext, guarded_writer: GuardedFileWriter, execution_scope: ExecutionScope):
    execution_scope.enter(governed_context)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            governed_context.metadata["ambient_root"] = str(root)
            writer = GuardedFileWriter(
                write_guard=guarded_writer.write_guard,
                root_resolver=RootResolver(),
                legacy_fallback=False,
            )
            path = writer.append_jsonl(
                "state/v044_test.jsonl",
                {"ok": True},
                target=WriteTarget.STATE,
                context=governed_context,
            )
            assert path.exists()
            lines = path.read_text().strip().splitlines()
            assert json.loads(lines[-1])["ok"] is True
    finally:
        execution_scope.exit(governed_context.context_id)


def test_append_denied_without_context(guarded_writer: GuardedFileWriter):
    with pytest.raises(PermissionError):
        guarded_writer.append_jsonl(
            "state/denied.jsonl",
            {"x": 1},
            target=WriteTarget.STATE,
            context=None,
        )
