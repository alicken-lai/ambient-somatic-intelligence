"""Callback scope — declared authority for bus/somatic hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContextInheritance(str, Enum):
    """How callbacks inherit ExecutionContext."""

    INHERIT = "inherit"
    ISOLATE = "isolate"
    CHILD = "child"


@dataclass(frozen=True)
class CallbackScope:
    source: str
    allowed_reads: frozenset[str] = field(default_factory=frozenset)
    allowed_writes: frozenset[str] = field(default_factory=frozenset)
    max_duration_seconds: float = 30.0
    inheritance: ContextInheritance = ContextInheritance.INHERIT

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "allowed_reads": sorted(self.allowed_reads),
            "allowed_writes": sorted(self.allowed_writes),
            "max_duration_seconds": self.max_duration_seconds,
            "inheritance": self.inheritance.value,
        }
