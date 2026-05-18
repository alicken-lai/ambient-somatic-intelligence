"""Execution isolation kernel — context-bound side effects (v0.4.3)."""

from kernel.isolation.callback_guard import CallbackGuard, RegisteredCallback
from kernel.isolation.callback_scope import CallbackScope, ContextInheritance
from kernel.isolation.execution_audit import AuditEntry, ExecutionAudit
from kernel.isolation.execution_context import (
    EscalationRequest,
    ExecutionContext,
    Permission,
)
from kernel.isolation.execution_identity import CallerType, ExecutionIdentity
from kernel.isolation.execution_result import ExecutionResult, ExecutionStatus
from kernel.isolation.execution_scope import ExecutionScope, ScopeType, ScopeViolation
from kernel.isolation.resource_guard import ResourceDenial, ResourceGuard
from kernel.isolation.rollback_boundary import RollbackBoundary
from kernel.isolation.rollback_plan import RollbackPlan, RollbackType
from kernel.isolation.root_policy import resolve_ambient_root
from kernel.isolation.root_resolver import RootResolver
from kernel.isolation.sandbox_context import SandboxContext
from kernel.isolation.sandbox_memory import SandboxMemory, SandboxEntry
from kernel.isolation.state_guard import StateGuard, WriteDenial
from kernel.isolation.write_guard import WriteGuard
from kernel.isolation.write_target import WriteTarget
from kernel.isolation.write_violation import WriteViolation
from kernel.isolation.governed_memory_writer import GovernedMemoryWriter
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.guarded_callback import GuardedCallback
from kernel.isolation.singleton_guard import SingletonGuard
from kernel.isolation.singleton_mutation import SingletonMutation
from kernel.isolation.registry_guard import RegistryGuard
from kernel.isolation.registry_mutation import RegistryMutation

__all__ = [
    "AuditEntry",
    "CallbackGuard",
    "CallbackScope",
    "CallerType",
    "ContextInheritance",
    "EscalationRequest",
    "ExecutionAudit",
    "ExecutionContext",
    "ExecutionIdentity",
    "ExecutionResult",
    "ExecutionScope",
    "ExecutionStatus",
    "Permission",
    "RegisteredCallback",
    "ResourceDenial",
    "ResourceGuard",
    "RollbackBoundary",
    "RollbackPlan",
    "RollbackType",
    "RootResolver",
    "SandboxContext",
    "SandboxEntry",
    "SandboxMemory",
    "ScopeType",
    "ScopeViolation",
    "StateGuard",
    "WriteDenial",
    "WriteGuard",
    "WriteTarget",
    "WriteViolation",
    "resolve_ambient_root",
    "GovernedMemoryWriter",
    "GuardedFileWriter",
    "GuardedCallback",
    "SingletonGuard",
    "SingletonMutation",
    "RegistryGuard",
    "RegistryMutation",
]
