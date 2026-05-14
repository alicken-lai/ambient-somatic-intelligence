"""
skills.core — Core infrastructure for the Ambient OS skill layer.

Exports the foundational types and services:
  - SkillSchema, SkillInput, SkillOutput, SkillMetadata, SkillContext, SkillResult
  - SkillRegistry
  - SkillRouter, RoutingDecision
  - SkillValidator, ValidationResult
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
]
