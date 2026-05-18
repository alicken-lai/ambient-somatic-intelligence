"""Authority trace — append-only isolation observability events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TraceEvent:
    event_type: str
    detail: str
    context_id: str | None = None
    target: str | None = None
    caller_id: str | None = None
    mutation_type: str | None = None
    rollback_type: str | None = None
    result: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "detail": self.detail,
            "context_id": self.context_id,
            "target": self.target,
            "caller_id": self.caller_id,
            "mutation_type": self.mutation_type,
            "rollback_type": self.rollback_type,
            "result": self.result,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class AuthorityTrace:
    """Collects isolation-related events for scoring."""

    def __init__(self, max_events: int = 2000) -> None:
        self._events: list[TraceEvent] = []
        self._max = max_events

    def record(
        self,
        event_type: str,
        detail: str,
        *,
        context_id: str | None = None,
        target: str | None = None,
        caller_id: str | None = None,
        mutation_type: str | None = None,
        rollback_type: str | None = None,
        result: str | None = None,
    ) -> None:
        self._events.append(
            TraceEvent(
                event_type=event_type,
                detail=detail,
                context_id=context_id,
                target=target,
                caller_id=caller_id,
                mutation_type=mutation_type,
                rollback_type=rollback_type,
                result=result,
            )
        )
        if len(self._events) > self._max:
            self._events = self._events[-self._max :]

    def record_guarded_operation(
        self,
        *,
        mutation_type: str,
        target: str,
        context_id: str | None = None,
        caller_id: str | None = None,
        rollback_type: str | None = None,
        result: str = "ok",
        detail: str = "",
    ) -> None:
        """Emit trace for a guarded mutation (v0.4.4)."""
        self.record(
            event_type="guarded_mutation",
            detail=detail or f"{mutation_type} → {target}",
            context_id=context_id,
            target=target,
            caller_id=caller_id,
            mutation_type=mutation_type,
            rollback_type=rollback_type,
            result=result,
        )

    def by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return counts

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events[-limit:]]
