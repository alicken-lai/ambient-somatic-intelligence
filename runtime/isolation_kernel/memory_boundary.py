"""
Memory Boundary — Per-task memory isolation preventing cross-agent leakage.

Each active task gets a MemoryBoundary scoped to its agent's IsolationPolicy.
The boundary enforces:
  - Write-layer restrictions (agent can only write to allowed layers)
  - Read-layer restrictions (agent can only read from readable layers)
  - Per-task write quotas (prevents runaway memory writes)
  - Write tracking with content hashes for auditability

MemoryBoundaryManager creates, tracks, and cleans up boundaries across tasks.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from runtime.isolation_kernel.boundary_definitions import (
    BoundaryRegistry,
    IsolationPolicy,
)

log = logging.getLogger(__name__)


@dataclass
class WriteCheckResult:
    allowed: bool
    layer: str
    reason: str
    remaining_quota: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "layer": self.layer,
            "reason": self.reason,
            "remaining_quota": self.remaining_quota,
        }


@dataclass
class ReadCheckResult:
    allowed: bool
    layer: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "layer": self.layer,
            "reason": self.reason,
        }


class MemoryBoundary:
    """Per-task memory boundary enforcing layer access and write quotas."""

    def __init__(
        self,
        agent_id: str,
        task_id: str,
        policy: IsolationPolicy,
    ) -> None:
        self._agent_id = agent_id
        self._task_id = task_id
        self._policy = policy
        self._write_count = 0
        self._write_hashes: list[dict[str, str]] = []

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def task_id(self) -> str:
        return self._task_id

    def check_write(self, layer: str, content: str) -> WriteCheckResult:
        remaining = self.get_remaining_quota()

        if layer not in self._policy.allowed_memory_layers:
            return WriteCheckResult(
                allowed=False,
                layer=layer,
                reason=(
                    f"Layer '{layer}' not in allowed write layers "
                    f"{self._policy.allowed_memory_layers}"
                ),
                remaining_quota=remaining,
            )

        if self.is_quota_exceeded():
            return WriteCheckResult(
                allowed=False,
                layer=layer,
                reason=(
                    f"Write quota exceeded: {self._write_count}/"
                    f"{self._policy.max_memory_writes_per_task}"
                ),
                remaining_quota=0,
            )

        return WriteCheckResult(
            allowed=True,
            layer=layer,
            reason=f"Write to '{layer}' permitted ({remaining} writes remaining)",
            remaining_quota=remaining,
        )

    def check_read(self, layer: str) -> ReadCheckResult:
        if layer in self._policy.readable_memory_layers:
            return ReadCheckResult(
                allowed=True,
                layer=layer,
                reason=f"Layer '{layer}' is in readable layers",
            )
        return ReadCheckResult(
            allowed=False,
            layer=layer,
            reason=(
                f"Layer '{layer}' not in readable layers "
                f"{self._policy.readable_memory_layers}"
            ),
        )

    def record_write(self, layer: str, content_hash: str) -> None:
        self._write_count += 1
        self._write_hashes.append({
            "layer": layer,
            "content_hash": content_hash,
            "sequence": self._write_count,
        })
        log.debug(
            "Memory write #%d for %s task %s → %s",
            self._write_count, self._agent_id, self._task_id, layer,
        )

    def get_write_count(self) -> int:
        return self._write_count

    def get_remaining_quota(self) -> int:
        return max(0, self._policy.max_memory_writes_per_task - self._write_count)

    def is_quota_exceeded(self) -> bool:
        return self._write_count >= self._policy.max_memory_writes_per_task

    def stats(self) -> dict[str, Any]:
        return {
            "agent_id": self._agent_id,
            "task_id": self._task_id,
            "write_count": self._write_count,
            "remaining_quota": self.get_remaining_quota(),
            "quota_limit": self._policy.max_memory_writes_per_task,
            "write_hashes": self._write_hashes,
        }


class MemoryBoundaryManager:
    """Creates, tracks, and cleans up per-task memory boundaries."""

    def __init__(self, registry: BoundaryRegistry) -> None:
        self._registry = registry
        self._active: dict[str, MemoryBoundary] = {}

    def create_boundary(self, agent_id: str, task_id: str) -> MemoryBoundary:
        policy = self._registry.get_policy(agent_id)
        boundary = MemoryBoundary(agent_id, task_id, policy)
        self._active[task_id] = boundary
        log.info("Created memory boundary for %s task %s", agent_id, task_id)
        return boundary

    def get_active_boundaries(self) -> list[MemoryBoundary]:
        return list(self._active.values())

    def cleanup_boundary(self, task_id: str) -> None:
        removed = self._active.pop(task_id, None)
        if removed:
            log.info(
                "Cleaned up memory boundary for %s task %s "
                "(writes: %d)",
                removed.agent_id, task_id, removed.get_write_count(),
            )

    def get_boundary(self, task_id: str) -> MemoryBoundary | None:
        return self._active.get(task_id)

    def stats(self) -> dict[str, Any]:
        return {
            "active_boundaries": len(self._active),
            "boundaries": {
                tid: b.stats() for tid, b in self._active.items()
            },
        }
