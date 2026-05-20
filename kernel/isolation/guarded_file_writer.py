"""Guarded file writer — append/write under ExecutionContext + WriteGuard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.root_resolver import RootResolver
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget

try:
    from observability.v04.authority_trace import AuthorityTrace
except ImportError:  # pragma: no cover
    AuthorityTrace = None  # type: ignore[misc, assignment]


class GuardedFileWriter:
    """
    Route file mutations through WriteGuard and RootResolver.

    Legacy callers may omit context; guarded paths require an active ExecutionContext.
    """

    def __init__(
        self,
        write_guard: WriteGuard | None = None,
        root_resolver: RootResolver | None = None,
        *,
        authority_trace: Any | None = None,
        legacy_fallback: bool = True,
    ) -> None:
        self.write_guard = write_guard or WriteGuard()
        self.root_resolver = root_resolver or RootResolver()
        self.authority_trace = authority_trace
        self.legacy_fallback = legacy_fallback

    def append_jsonl(
        self,
        relative: str | Path,
        record: dict[str, Any],
        *,
        target: WriteTarget | str,
        context: ExecutionContext | None = None,
    ) -> Path:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"

        def _write() -> Path:
            path = self.root_resolver.resolve_path(context, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line)
            return path

        return self._guarded_io(
            target,
            _write,
            context=context,
            mutation_type="FILE_WRITE",
        )

    def write_text(
        self,
        relative: str | Path,
        content: str,
        *,
        target: WriteTarget | str,
        context: ExecutionContext | None = None,
        encoding: str = "utf-8",
    ) -> Path:
        def _write() -> Path:
            return self.root_resolver.write_text(context, relative, content, encoding=encoding)

        return self._guarded_io(
            target,
            _write,
            context=context,
            mutation_type="FILE_WRITE",
        )

    def _guarded_io(
        self,
        target: WriteTarget | str,
        fn: Callable[[], Path],
        *,
        context: ExecutionContext | None,
        mutation_type: str,
    ) -> Path:
        ctx = context or self.write_guard.scope.current()
        if ctx is None:
            if self.legacy_fallback:
                return fn()
            self.write_guard.assert_write(target, context=context)

        try:
            result = self.write_guard.guarded_write(target, fn, context=ctx)
            self._trace(ctx, target, mutation_type, "allow")
            return result
        except PermissionError:
            self._trace(ctx, target, mutation_type, "deny")
            raise

    def _trace(
        self,
        context: ExecutionContext | None,
        target: WriteTarget | str,
        mutation_type: str,
        result: str,
    ) -> None:
        if self.authority_trace is None or AuthorityTrace is None:
            return
        if hasattr(self.authority_trace, "record_guarded_operation"):
            self.authority_trace.record_guarded_operation(
                mutation_type=mutation_type,
                target=str(target.value if isinstance(target, WriteTarget) else target),
                context_id=context.context_id if context else None,
                caller_id=context.caller_id if context else None,
                result=result,
            )
