"""Execution context — mandatory envelope for all side-effecting operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from kernel.isolation.execution_identity import CallerType, ExecutionIdentity
from kernel.isolation.rollback_plan import RollbackPlan
from kernel.isolation.write_target import WriteTarget


class Permission(str, Enum):
    """Capabilities granted within an execution context."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    GOVERNANCE = "governance"


def _default_expires(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


@dataclass(frozen=True)
class ExecutionContext:
    """
    Mandatory context for any kernel execution with side effects.

    Rules:
      - No execution without context
      - No cross-context writes
      - Scope escalation requires Guardian reference
    """

    context_id: str
    caller_id: str
    caller_type: CallerType
    scope: str
    permissions: frozenset[Permission]
    phase: str = "runtime"
    allowed_read_targets: frozenset[str] = field(default_factory=frozenset)
    allowed_write_targets: frozenset[str] = field(default_factory=frozenset)
    allowed_resources: frozenset[str] = field(default_factory=frozenset)
    rollback_boundaries: tuple[str, ...] = ()
    rollback_plan: RollbackPlan | None = None
    guardian_reference: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: str = field(default_factory=_default_expires)
    metadata: dict[str, Any] = field(default_factory=dict)
    identity: ExecutionIdentity | None = None

    # Backward-compatible aliases (v0.4)
    @property
    def caller(self) -> str:
        return self.caller_id

    @property
    def write_targets(self) -> frozenset[str]:
        return self.allowed_write_targets

    def __post_init__(self) -> None:
        if not self.caller_id or not self.caller_id.strip():
            raise ValueError("ExecutionContext.caller_id is required")
        if not self.scope or not self.scope.strip():
            raise ValueError("ExecutionContext.scope is required")
        if not self.permissions:
            raise ValueError("ExecutionContext.permissions must be non-empty")
        if self.is_expired():
            raise ValueError(f"ExecutionContext {self.context_id} already expired")

    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > exp
        except ValueError:
            return False

    @classmethod
    def create(
        cls,
        *,
        caller: str | None = None,
        caller_id: str | None = None,
        caller_type: CallerType | str = CallerType.UNKNOWN,
        scope: str,
        permissions: set[Permission] | frozenset[Permission],
        phase: str = "runtime",
        allowed_resources: set[str] | frozenset[str] | None = None,
        allowed_read_targets: set[str] | frozenset[str] | None = None,
        write_targets: set[str] | frozenset[str] | None = None,
        allowed_write_targets: set[str] | frozenset[str] | None = None,
        rollback_boundaries: tuple[str, ...] | None = None,
        rollback_plan: RollbackPlan | None = None,
        guardian_reference: str | None = None,
        expires_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        cid = caller_id or caller
        if not cid:
            raise ValueError("caller_id or caller is required")
        ct = caller_type if isinstance(caller_type, CallerType) else CallerType(caller_type)
        writes = allowed_write_targets or write_targets or frozenset()
        identity = ExecutionIdentity(caller_id=cid, caller_type=ct, phase=phase)
        return cls(
            context_id=str(uuid.uuid4()),
            caller_id=cid,
            caller_type=ct,
            scope=scope,
            permissions=frozenset(permissions),
            phase=phase,
            allowed_read_targets=frozenset(allowed_read_targets or ()),
            allowed_write_targets=frozenset(writes),
            allowed_resources=frozenset(allowed_resources or ()),
            rollback_boundaries=rollback_boundaries or (),
            rollback_plan=rollback_plan,
            guardian_reference=guardian_reference,
            expires_at=expires_at or _default_expires(),
            metadata=metadata or {},
            identity=identity,
        )

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def can_read(self, target: str) -> bool:
        if not self.has_permission(Permission.READ):
            return False
        if not self.allowed_read_targets:
            return True
        return target in self.allowed_read_targets

    def can_write(self, target: str) -> bool:
        if not self.has_permission(Permission.WRITE):
            return False
        if not self.allowed_write_targets:
            return True
        return target in self.allowed_write_targets

    def can_access(self, resource: str) -> bool:
        if not self.allowed_resources:
            return True
        return resource in self.allowed_resources

    def request_escalation(
        self,
        new_scope: str,
        guardian_reference: str,
    ) -> EscalationRequest:
        return EscalationRequest(
            from_context_id=self.context_id,
            from_scope=self.scope,
            to_scope=new_scope,
            caller=self.caller_id,
            guardian_reference=guardian_reference,
        )

    def with_write_targets(self, *targets: WriteTarget | str) -> ExecutionContext:
        merged = set(self.allowed_write_targets) | {
            t.value if isinstance(t, WriteTarget) else t for t in targets
        }
        return ExecutionContext(
            context_id=self.context_id,
            caller_id=self.caller_id,
            caller_type=self.caller_type,
            scope=self.scope,
            permissions=self.permissions,
            phase=self.phase,
            allowed_read_targets=self.allowed_read_targets,
            allowed_write_targets=frozenset(merged),
            allowed_resources=self.allowed_resources,
            rollback_boundaries=self.rollback_boundaries,
            rollback_plan=self.rollback_plan,
            guardian_reference=self.guardian_reference,
            created_at=self.created_at,
            expires_at=self.expires_at,
            metadata=dict(self.metadata),
            identity=self.identity,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "caller_id": self.caller_id,
            "caller": self.caller_id,
            "caller_type": self.caller_type.value,
            "scope": self.scope,
            "phase": self.phase,
            "permissions": sorted(p.value for p in self.permissions),
            "allowed_read_targets": sorted(self.allowed_read_targets),
            "allowed_write_targets": sorted(self.allowed_write_targets),
            "write_targets": sorted(self.allowed_write_targets),
            "allowed_resources": sorted(self.allowed_resources),
            "rollback_boundaries": list(self.rollback_boundaries),
            "rollback_plan": self.rollback_plan.to_dict() if self.rollback_plan else None,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "guardian_reference": self.guardian_reference,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EscalationRequest:
    """Recorded intent to escalate scope — requires Guardian approval out-of-band."""

    from_context_id: str
    from_scope: str
    to_scope: str
    caller: str
    guardian_reference: str
    requested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, str]:
        return {
            "from_context_id": self.from_context_id,
            "from_scope": self.from_scope,
            "to_scope": self.to_scope,
            "caller": self.caller,
            "guardian_reference": self.guardian_reference,
            "requested_at": self.requested_at,
        }
