"""Execution identity — stable caller identification for isolation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CallerType(str, Enum):
    """Classification of execution callers."""

    AGENT = "agent"
    DAEMON = "daemon"
    KERNEL = "kernel"
    TASK = "task"
    CALLBACK = "callback"
    HUMAN = "human"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ExecutionIdentity:
    """Immutable identity bundle attached to an ExecutionContext."""

    caller_id: str
    caller_type: CallerType
    phase: str = "runtime"
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.caller_id or not self.caller_id.strip():
            raise ValueError("ExecutionIdentity.caller_id is required")

    @property
    def display(self) -> str:
        return f"{self.caller_type.value}:{self.caller_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "caller_id": self.caller_id,
            "caller_type": self.caller_type.value,
            "phase": self.phase,
            "labels": list(self.labels),
        }

    @classmethod
    def from_caller(
        cls,
        caller: str,
        *,
        caller_type: CallerType | str = CallerType.UNKNOWN,
        phase: str = "runtime",
    ) -> ExecutionIdentity:
        ct = caller_type if isinstance(caller_type, CallerType) else CallerType(caller_type)
        return cls(caller_id=caller, caller_type=ct, phase=phase)
