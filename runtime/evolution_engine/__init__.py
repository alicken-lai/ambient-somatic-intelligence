"""
Evolution Engine — Phase H of Ambient OS Architecture.

Controlled self-refactoring: the system can propose improvements
to its own architecture, simulate them, benchmark them, and package
them for human review — but NEVER apply them autonomously.

  patch_proposer.py     — Generate refactoring proposals from analysis
  refactor_planner.py   — Plan refactoring with dependency awareness
  mutation_simulator.py — Simulate mutations without applying
  rollback_planner.py   — Plan rollbacks for every evolution step
  evolution_engine.py   — Unified orchestration of the evolution pipeline
  audit_logger.py       — Immutable audit trail for evolution activities

Safety constraints:
  - May PROPOSE, SIMULATE, BENCHMARK, COMPARE
  - May NOT self-deploy, auto-merge, bypass review, mutate production runtime
  - All proposals require governance approval + audit logging + rollback strategy
"""

from runtime.evolution_engine.patch_proposer import (
    PatchProposer,
    PatchProposal,
    PatchType,
)
from runtime.evolution_engine.refactor_planner import (
    RefactorPlanner,
    RefactorPlan,
    RefactorStep,
)
from runtime.evolution_engine.mutation_simulator import (
    MutationSimulator,
    SimulationResult,
    SystemTopology,
    ComparisonReport,
)
from runtime.evolution_engine.rollback_planner import (
    RollbackPlanner,
    RollbackPlan,
    RollbackStep,
    RollbackValidation,
)
from runtime.evolution_engine.evolution_engine import (
    EvolutionEngine,
    EvolutionStatus,
    EvolutionProposalPacket,
    BenchmarkResult,
    RiskAssessment,
)
from runtime.evolution_engine.audit_logger import (
    EvolutionAuditLogger,
    EvolutionAuditEntry,
    AuditAction,
)

__all__ = [
    # Patch Proposer
    "PatchProposer",
    "PatchProposal",
    "PatchType",
    # Refactor Planner
    "RefactorPlanner",
    "RefactorPlan",
    "RefactorStep",
    # Mutation Simulator
    "MutationSimulator",
    "SimulationResult",
    "SystemTopology",
    "ComparisonReport",
    # Rollback Planner
    "RollbackPlanner",
    "RollbackPlan",
    "RollbackStep",
    "RollbackValidation",
    # Evolution Engine
    "EvolutionEngine",
    "EvolutionStatus",
    "EvolutionProposalPacket",
    "BenchmarkResult",
    "RiskAssessment",
    # Audit Logger
    "EvolutionAuditLogger",
    "EvolutionAuditEntry",
    "AuditAction",
]
