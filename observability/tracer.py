"""
Execution Tracer — Distributed tracing for the Ambient OS cognitive runtime.

Provides OpenTelemetry-inspired tracing:
  - Traces span the full lifecycle of a task (user request → response)
  - Spans capture individual operations (memory recall, governance check, etc.)
  - Parent-child relationships form a tree
  - Cross-layer correlation via trace_id

Example trace:
  [Trace: user_request_abc]
    ├─ [Span: context_assembly] 45ms
    │   ├─ [Span: memory_recall] 12ms
    │   └─ [Span: budget_check] 3ms
    ├─ [Span: guardian_check] 8ms
    ├─ [Span: task_execution] 2300ms
    │   ├─ [Span: subagent_frontend] 1200ms
    │   └─ [Span: subagent_backend] 1800ms
    └─ [Span: memory_writeback] 15ms
"""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Generator


TRACES_DIR = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os")) / "observability" / "traces"


class SpanKind(str, Enum):
    INTERNAL = "internal"
    TASK = "task"
    AGENT = "agent"
    MEMORY = "memory"
    GOVERNANCE = "governance"
    CONTEXT = "context"
    SOMATIC = "somatic"
    EXTERNAL = "external"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class Span:
    """A single unit of work within a trace."""
    name: str
    kind: SpanKind
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    status: SpanStatus = SpanStatus.OK
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return round((self.end_time - self.start_time) * 1000, 2)

    @property
    def is_active(self) -> bool:
        return self.end_time is None

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def end(self, status: SpanStatus = SpanStatus.OK) -> None:
        self.end_time = time.time()
        self.status = status

    def end_error(self, error: str) -> None:
        self.end_time = time.time()
        self.status = SpanStatus.ERROR
        self.attributes["error"] = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time, tz=timezone.utc).isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events,
        }


@dataclass
class Trace:
    """A collection of related spans forming a complete execution path."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:32])
    root_span: Span | None = None
    spans: list[Span] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.root_span:
            return self.root_span.duration_ms
        if self.spans:
            start = min(s.start_time for s in self.spans)
            ends = [s.end_time for s in self.spans if s.end_time]
            if ends:
                return round((max(ends) - start) * 1000, 2)
        return None

    @property
    def span_count(self) -> int:
        return len(self.spans)

    @property
    def error_count(self) -> int:
        return sum(1 for s in self.spans if s.status == SpanStatus.ERROR)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "duration_ms": self.duration_ms,
            "span_count": self.span_count,
            "error_count": self.error_count,
            "metadata": self.metadata,
            "spans": [s.to_dict() for s in self.spans],
        }

    def tree_view(self, indent: int = 0) -> str:
        """Generate ASCII tree view of trace spans."""
        lines = []
        root_spans = [s for s in self.spans if s.parent_id is None]
        for span in root_spans:
            lines.extend(self._render_span(span, indent))
        return "\n".join(lines)

    def _render_span(self, span: Span, indent: int) -> list[str]:
        prefix = "  " * indent
        status_icon = {"ok": "+", "error": "!", "cancelled": "~"}.get(span.status.value, "?")
        dur = f"{span.duration_ms:.0f}ms" if span.duration_ms else "active"
        line = f"{prefix}[{status_icon}] {span.name} ({span.kind.value}) {dur}"
        lines = [line]

        children = [s for s in self.spans if s.parent_id == span.span_id]
        for child in children:
            lines.extend(self._render_span(child, indent + 1))
        return lines


class ExecutionTracer:
    """
    Manages traces and spans across the system.

    Usage:
        tracer = ExecutionTracer()

        # Start a trace
        with tracer.trace("user_request") as trace:
            with tracer.span("memory_recall", SpanKind.MEMORY) as span:
                span.set_attribute("query", "recent tasks")
                results = recall(query)
                span.set_attribute("results_count", len(results))

            with tracer.span("task_execution", SpanKind.TASK) as span:
                execute_task()

        # Inspect
        print(trace.tree_view())
    """

    def __init__(self, persist: bool = True, max_traces: int = 50):
        self._active_trace: Trace | None = None
        self._active_spans: list[Span] = []
        self._completed_traces: list[Trace] = []
        self._max_traces = max_traces
        self._persist = persist

        if persist:
            TRACES_DIR.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def trace(self, name: str, metadata: dict[str, Any] | None = None) -> Generator[Trace, None, None]:
        """Start a new trace context."""
        t = Trace(metadata=metadata or {})
        t.metadata["name"] = name
        self._active_trace = t

        root = Span(name=name, kind=SpanKind.INTERNAL, trace_id=t.trace_id)
        t.root_span = root
        t.spans.append(root)
        self._active_spans.append(root)

        try:
            yield t
            root.end(SpanStatus.OK)
        except Exception as e:
            root.end_error(str(e))
            raise
        finally:
            self._active_spans.pop()
            self._active_trace = None
            self._completed_traces.append(t)
            if len(self._completed_traces) > self._max_traces:
                self._completed_traces = self._completed_traces[-self._max_traces:]
            if self._persist:
                self._persist_trace(t)

    @contextmanager
    def span(self, name: str, kind: SpanKind = SpanKind.INTERNAL) -> Generator[Span, None, None]:
        """Start a child span within the active trace."""
        if not self._active_trace:
            s = Span(name=name, kind=kind, trace_id="orphan")
            try:
                yield s
                s.end()
            except Exception as e:
                s.end_error(str(e))
                raise
            return

        parent_id = self._active_spans[-1].span_id if self._active_spans else None
        s = Span(
            name=name,
            kind=kind,
            trace_id=self._active_trace.trace_id,
            parent_id=parent_id,
        )
        self._active_trace.spans.append(s)
        self._active_spans.append(s)

        try:
            yield s
            s.end(SpanStatus.OK)
        except Exception as e:
            s.end_error(str(e))
            raise
        finally:
            self._active_spans.pop()

    def recent_traces(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent completed traces."""
        return [t.to_dict() for t in self._completed_traces[-limit:]]

    def find_trace(self, trace_id: str) -> Trace | None:
        """Find a trace by ID."""
        for t in self._completed_traces:
            if t.trace_id == trace_id:
                return t
        return None

    def stats(self) -> dict[str, Any]:
        """Get tracing statistics."""
        total_spans = sum(t.span_count for t in self._completed_traces)
        total_errors = sum(t.error_count for t in self._completed_traces)
        durations = [t.duration_ms for t in self._completed_traces if t.duration_ms]

        return {
            "total_traces": len(self._completed_traces),
            "total_spans": total_spans,
            "total_errors": total_errors,
            "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "active_trace": self._active_trace.trace_id if self._active_trace else None,
        }

    def _persist_trace(self, trace: Trace) -> None:
        """Save trace to disk as JSON-lines."""
        try:
            filepath = TRACES_DIR / f"trace_{trace.trace_id[:12]}.jsonl"
            with open(filepath, "a") as f:
                f.write(json.dumps(trace.to_dict()) + "\n")
        except OSError:
            pass
