"""
skills — Formal Skill Layer for Ambient OS.

The skill layer provides:
  - Typed skill schemas with formal input/output contracts
  - A central registry for discovery and lifecycle management
  - A router for task-to-skill matching with governance checks
  - Schema and execution validation
  - Legacy script compatibility adapter
  - Built-in skills for system, sensing, cognition, and governance

Quick start:
    from skills.core import SkillRegistry, SkillRouter
    from skills.system import anomaly_explain_skill

    registry = SkillRegistry()
    registry.register(anomaly_explain_skill)

    router = SkillRouter(registry)
    decision = router.route("explain the current anomaly")
"""

from __future__ import annotations

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillResult,
    SkillSchema,
)
from skills.core.skill_registry import SkillRegistry
from skills.core.skill_router import RoutingDecision, SkillRouter
from skills.core.skill_validator import SkillValidator, ValidationResult
from skills.compat import wrap_legacy_script

__all__ = [
    "SkillContext",
    "SkillInput",
    "SkillMetadata",
    "SkillOutput",
    "SkillResult",
    "SkillSchema",
    "SkillRegistry",
    "SkillRouter",
    "RoutingDecision",
    "SkillValidator",
    "ValidationResult",
    "wrap_legacy_script",
]
