"""
Task Graph Runtime — Phase 3 of Ambient OS Architecture Refactor.

A dependency-aware DAG (Directed Acyclic Graph) runtime that replaces
the flat action_router with structured task orchestration:

  dag.py        — Task nodes, edges, and graph structure
  scheduler.py  — Topological sort, parallel dispatch, blocking conditions
  checkpoint.py — Execution snapshots, rollback, recovery
  executor.py   — Task execution engine with retry policies

The task graph ensures correct execution ordering, parallel execution
of independent tasks, and safe rollback on failure.
"""

from runtime.task_graph.dag import TaskGraph, TaskNode, TaskStatus, TaskEdge
from runtime.task_graph.scheduler import Scheduler
from runtime.task_graph.checkpoint import CheckpointManager
from runtime.task_graph.executor import TaskExecutor

__all__ = [
    "TaskGraph",
    "TaskNode",
    "TaskStatus",
    "TaskEdge",
    "Scheduler",
    "CheckpointManager",
    "TaskExecutor",
]
