"""
Execution Isolation Kernel — Eliminates implicit shared state across agents.

All inter-agent communication must pass through governed channels. Each agent
operates within a sandbox defined by its IsolationPolicy, enforced at the
memory, tool, context, and state-access levels.

Components:
  boundary_definitions  — IsolationPolicy, BoundaryRegistry, default policies
  execution_sandbox     — Per-agent task sandbox with governance gate integration
  memory_boundary       — Per-task memory write/read enforcement and quotas
  context_firewall      — Cross-task context filtering and token budget caps
  permission_enforcer   — Runtime tool and interaction permission checks
"""

from runtime.isolation_kernel.boundary_definitions import (
    IsolationPolicy,
    BoundaryCheckResult,
    BoundaryRegistry,
    DEFAULT_AGENT_POLICIES,
)
from runtime.isolation_kernel.execution_sandbox import (
    ExecutionSandbox,
    SandboxManager,
    SandboxResult,
    SandboxAuditRecord,
    GateCheckResult,
)
from runtime.isolation_kernel.memory_boundary import (
    MemoryBoundary,
    MemoryBoundaryManager,
    WriteCheckResult,
    ReadCheckResult,
)
from runtime.isolation_kernel.context_firewall import (
    ContextFirewall,
    FilterResult,
    InjectionCheckResult,
    BudgetCheckResult,
)
from runtime.isolation_kernel.permission_enforcer import (
    PermissionEnforcer,
    ToolAccessResult,
    InteractionResult,
    StateAccessResult,
    EnforcementReport,
)

__all__ = [
    "IsolationPolicy",
    "BoundaryCheckResult",
    "BoundaryRegistry",
    "DEFAULT_AGENT_POLICIES",
    "ExecutionSandbox",
    "SandboxManager",
    "SandboxResult",
    "SandboxAuditRecord",
    "GateCheckResult",
    "MemoryBoundary",
    "MemoryBoundaryManager",
    "WriteCheckResult",
    "ReadCheckResult",
    "ContextFirewall",
    "FilterResult",
    "InjectionCheckResult",
    "BudgetCheckResult",
    "PermissionEnforcer",
    "ToolAccessResult",
    "InteractionResult",
    "StateAccessResult",
    "EnforcementReport",
]
