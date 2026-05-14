"""
Cognitive Self-Model — Ambient OS identity layer for self-introspection.

Provides a queryable model of the system's own architecture, dependencies,
memory structure, and governance boundaries. The self-model enables the system
to understand its own structure, detect drift, and report health.

Components:
  architecture_graph.py — Subsystem/module/class topology via AST introspection
  dependency_graph.py   — Runtime dependency analysis with cycle detection
  memory_topology.py    — Memory layer mapping with health scoring
  governance_map.py     — Governance boundary and permission mapping
  self_model.py         — Unified composition of all sub-models
"""

from identity.cognitive_self_model.architecture_graph import (
    ArchitectureGraph,
    SubsystemNode,
    ModuleNode,
    ClassNode,
    TopologySnapshot,
)
from identity.cognitive_self_model.dependency_graph import (
    DependencyGraph,
    DependencyEdge,
    CyclePath,
)
from identity.cognitive_self_model.memory_topology import (
    MemoryTopology,
    LayerInfo,
    LayerHealth,
)
from identity.cognitive_self_model.governance_map import (
    GovernanceMap,
    GovernanceBoundary,
    PermissionSummary,
    PolicyRule,
)
from identity.cognitive_self_model.self_model import (
    CognitiveSelfModel,
    SelfModelHealth,
)

__all__ = [
    "ArchitectureGraph",
    "SubsystemNode",
    "ModuleNode",
    "ClassNode",
    "TopologySnapshot",
    "DependencyGraph",
    "DependencyEdge",
    "CyclePath",
    "MemoryTopology",
    "LayerInfo",
    "LayerHealth",
    "GovernanceMap",
    "GovernanceBoundary",
    "PermissionSummary",
    "PolicyRule",
    "CognitiveSelfModel",
    "SelfModelHealth",
]
