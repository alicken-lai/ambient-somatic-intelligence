"""
Skill Validator — Validate skill definitions and execution results.

Ensures every skill meets the formal contract before registration and
verifies that execution results conform to declared outputs and memory
side effects.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from skills.core.skill_schema import SkillResult, SkillSchema

logger = logging.getLogger(__name__)

VALID_GOVERNANCE_LEVELS = {"ALLOW", "REVIEW_REQUIRED", "BLOCK_WITHOUT_APPROVAL"}
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class SkillValidator:
    """
    Validates skill schemas before registration and execution results
    against declared contracts.

    Usage:
        validator = SkillValidator()
        result = validator.validate_schema(my_skill)
        if not result.valid:
            print(result.errors)
    """

    def validate_schema(self, skill: SkillSchema) -> ValidationResult:
        """Validate a skill definition before registration."""
        errors: list[str] = []
        warnings: list[str] = []

        if not skill.name or not skill.name.strip():
            errors.append("Skill must have a non-empty name")

        if not skill.version or not skill.version.strip():
            errors.append("Skill must have a non-empty version")
        elif not SEMVER_PATTERN.match(skill.version):
            warnings.append(
                f"Version '{skill.version}' does not follow semver (x.y.z)"
            )

        if not skill.description or not skill.description.strip():
            errors.append("Skill must have a non-empty description")

        if skill.governance_level not in VALID_GOVERNANCE_LEVELS:
            errors.append(
                f"Invalid governance_level '{skill.governance_level}'; "
                f"must be one of {sorted(VALID_GOVERNANCE_LEVELS)}"
            )

        if not skill.inputs:
            errors.append("Skill must declare at least one input")

        if not skill.outputs:
            errors.append("Skill must declare at least one output")

        if not callable(skill.execute):
            errors.append("Skill must have a callable 'execute' function")

        lo, hi = skill.confidence_range
        if not (0.0 <= lo <= hi <= 1.0):
            errors.append(
                f"confidence_range ({lo}, {hi}) must satisfy 0 <= min <= max <= 1"
            )

        seen_inputs: set[str] = set()
        for inp in skill.inputs:
            if inp.name in seen_inputs:
                errors.append(f"Duplicate input name: '{inp.name}'")
            seen_inputs.add(inp.name)

        seen_outputs: set[str] = set()
        for out in skill.outputs:
            if out.name in seen_outputs:
                errors.append(f"Duplicate output name: '{out.name}'")
            seen_outputs.add(out.name)

        if not skill.routing_conditions:
            warnings.append("No routing_conditions defined; skill will not be auto-routed")

        if not skill.memory_updates:
            warnings.append("No memory_updates declared; skill has no declared side effects")

        if not skill.observability_hooks:
            warnings.append("No observability_hooks declared")

        valid = len(errors) == 0
        if not valid:
            logger.warning(
                "Schema validation failed for skill '%s': %s", skill.name, errors,
            )
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)

    def validate_execution(
        self, skill: SkillSchema, result: SkillResult,
    ) -> ValidationResult:
        """Validate that execution results match the declared skill schema."""
        errors: list[str] = []
        warnings: list[str] = []

        if result.success:
            declared_outputs = {o.name for o in skill.outputs}
            actual_outputs = set(result.outputs.keys())
            missing = declared_outputs - actual_outputs
            if missing:
                warnings.append(f"Declared outputs missing from result: {sorted(missing)}")
            extra = actual_outputs - declared_outputs
            if extra:
                warnings.append(f"Undeclared outputs in result: {sorted(extra)}")

        if not result.trace_id:
            errors.append("Execution result must include a trace_id")

        if result.execution_time_ms < 0:
            errors.append("execution_time_ms cannot be negative")

        if not (0.0 <= result.confidence <= 1.0):
            errors.append(
                f"Result confidence {result.confidence} must be between 0.0 and 1.0"
            )

        valid = len(errors) == 0
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)

    def validate_memory_effects(
        self, declared: list[str], actual: list[str],
    ) -> ValidationResult:
        """Verify that actual memory side effects match declarations."""
        errors: list[str] = []
        warnings: list[str] = []

        declared_set = set(declared)
        actual_set = set(actual)

        undeclared = actual_set - declared_set
        if undeclared:
            errors.append(
                f"Undeclared memory side effects: {sorted(undeclared)}"
            )

        unused = declared_set - actual_set
        if unused:
            warnings.append(
                f"Declared memory effects not produced: {sorted(unused)}"
            )

        valid = len(errors) == 0
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
