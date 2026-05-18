"""Sandbox memory — in-memory store isolated from production DMN."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SandboxEntry:
    key: str
    value: Any
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SandboxMemory:
    """Ephemeral key-value store for sandboxed executions."""

    def __init__(self) -> None:
        self._store: dict[str, SandboxEntry] = {}

    @property
    def entries(self) -> list[SandboxEntry]:
        return list(self._store.values())

    def write(self, key: str, value: Any) -> None:
        self._store[key] = SandboxEntry(key=key, value=value)

    def read(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        return entry.value if entry else default

    def clear(self) -> None:
        self._store.clear()

    def to_dict(self) -> dict[str, Any]:
        return {k: v.value for k, v in self._store.items()}
