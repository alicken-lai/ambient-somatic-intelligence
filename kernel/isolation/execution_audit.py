"""Execution audit — append-only log of context lifecycle and denials."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from kernel.isolation.execution_context import ExecutionContext, EscalationRequest


@dataclass
class AuditEntry:
    event_type: str
    context_id: str
    caller: str
    scope: str
    detail: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "context_id": self.context_id,
            "caller": self.caller,
            "scope": self.scope,
            "detail": self.detail,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class ExecutionAudit:
    """Append-only audit trail for execution isolation events."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._entries: list[AuditEntry] = []
        self._max_entries = max_entries

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def _append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def log_enter(self, context: ExecutionContext) -> None:
        self._append(
            AuditEntry(
                event_type="context_enter",
                context_id=context.context_id,
                caller=context.caller,
                scope=context.scope,
                detail=f"permissions={[p.value for p in context.permissions]}",
            )
        )

    def log_exit(self, context: ExecutionContext) -> None:
        self._append(
            AuditEntry(
                event_type="context_exit",
                context_id=context.context_id,
                caller=context.caller,
                scope=context.scope,
                detail="context deactivated",
            )
        )

    def log_denial(self, context_id: str, caller: str, scope: str, reason: str) -> None:
        self._append(
            AuditEntry(
                event_type="access_denied",
                context_id=context_id,
                caller=caller,
                scope=scope,
                detail=reason,
            )
        )

    def log_escalation(self, request: EscalationRequest) -> None:
        self._append(
            AuditEntry(
                event_type="scope_escalation_requested",
                context_id=request.from_context_id,
                caller=request.caller,
                scope=request.to_scope,
                detail=f"guardian_ref={request.guardian_reference}",
            )
        )

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._entries[-limit:]]

    def stats(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for entry in self._entries:
            by_type[entry.event_type] = by_type.get(entry.event_type, 0) + 1
        return {"total": len(self._entries), "by_type": by_type}
