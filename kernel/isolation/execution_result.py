"""Execution result — structured outcome for isolated operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    DENIED = "denied"
    SANDBOXED = "sandboxed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class ExecutionResult(Generic[T]):
    """Outcome of an isolated execution with audit metadata."""

    status: ExecutionStatus
    context_id: str | None = None
    value: T | None = None
    error: str | None = None
    violations: list[str] = field(default_factory=list)
    sandboxed: bool = False
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def ok(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "context_id": self.context_id,
            "ok": self.ok,
            "error": self.error,
            "violations": self.violations,
            "sandboxed": self.sandboxed,
            "completed_at": self.completed_at,
        }
