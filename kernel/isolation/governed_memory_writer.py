"""Governed memory writer — DMN/layer writes under ExecutionContext (v0.4.4B)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.write_target import WriteTarget

try:
    from observability.v04.authority_trace import AuthorityTrace
except ImportError:  # pragma: no cover
    AuthorityTrace = None  # type: ignore[misc, assignment]


class GovernedMemoryWriter:
    """
    Route memory/DMN/replay writes through GuardedFileWriter with trace.

    Legacy callers omit context; governed path requires ExecutionContext.
    """

    def __init__(
        self,
        memory_root: Path | None = None,
        *,
        guarded_writer: GuardedFileWriter | None = None,
        authority_trace: Any | None = None,
        legacy_fallback: bool = True,
    ) -> None:
        import os

        ambient = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
        self.memory_root = memory_root or (ambient / "memory")
        self.guarded_writer = guarded_writer or GuardedFileWriter(
            authority_trace=authority_trace,
            legacy_fallback=legacy_fallback,
        )
        self.authority_trace = authority_trace

    def append_dmn(
        self,
        record: dict[str, Any],
        *,
        context: ExecutionContext | None = None,
        caller_id: str | None = None,
        mutation_reason: str = "dmn_append",
        rollback_type: RollbackType = RollbackType.COMPENSATING_WRITE,
    ) -> Path:
        return self._append_jsonl(
            "memory/dmn.jsonl",
            record,
            target=WriteTarget.MEMORY,
            context=context,
            caller_id=caller_id,
            mutation_reason=mutation_reason,
            rollback_type=rollback_type,
        )

    def append_layer(
        self,
        layer: str,
        record: dict[str, Any],
        *,
        context: ExecutionContext | None = None,
        caller_id: str | None = None,
        mutation_reason: str = "layer_store",
        rollback_type: RollbackType = RollbackType.COMPENSATING_WRITE,
    ) -> Path:
        rel = f"memory/{layer}/records.jsonl"
        return self._append_jsonl(
            rel,
            record,
            target=WriteTarget.MEMORY,
            context=context,
            caller_id=caller_id,
            mutation_reason=mutation_reason,
            rollback_type=rollback_type,
        )

    def _append_jsonl(
        self,
        relative: str,
        record: dict[str, Any],
        *,
        target: WriteTarget,
        context: ExecutionContext | None,
        caller_id: str | None,
        mutation_reason: str,
        rollback_type: RollbackType,
    ) -> Path:
        ctx = context
        if ctx is None and caller_id:
            from kernel.isolation.execution_context import Permission
            from kernel.isolation.execution_scope import ScopeType

            ctx = ExecutionContext.create(
                caller_id=caller_id,
                caller_type="memory",
                scope=ScopeType.GOVERNED_WRITE.value,
                permissions={Permission.READ, Permission.WRITE},
                allowed_write_targets={target.value},
                rollback_plan=RollbackPlan(rollback_type=rollback_type),
            )

        if ctx is not None:
            path = self.guarded_writer.append_jsonl(
                relative,
                record,
                target=target,
                context=ctx,
            )
            self._emit_trace(ctx, relative, mutation_reason, rollback_type)
            return path

        path = self.memory_root.parent / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return path

    def _emit_trace(
        self,
        context: ExecutionContext,
        target: str,
        mutation_reason: str,
        rollback_type: RollbackType,
    ) -> None:
        if self.authority_trace is None or not hasattr(
            self.authority_trace, "record_guarded_operation"
        ):
            return
        self.authority_trace.record_guarded_operation(
            mutation_type="MEMORY_WRITE",
            target=target,
            context_id=context.context_id,
            caller_id=context.caller_id,
            rollback_type=rollback_type.value,
            result="ok",
            detail=mutation_reason,
        )
