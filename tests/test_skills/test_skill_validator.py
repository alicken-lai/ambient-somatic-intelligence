"""Tests for skills.core.skill_validator — Valid/invalid skill rejection."""

from __future__ import annotations

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillOutput,
    SkillResult,
    SkillSchema,
)
from skills.core.skill_validator import SkillValidator


def _noop(ctx: SkillContext) -> SkillResult:
    return SkillResult(success=True)


def _valid_skill(**overrides) -> SkillSchema:
    defaults = dict(
        name="valid-skill",
        version="1.0.0",
        description="A valid skill",
        inputs=[SkillInput("x", "str", True, "input")],
        outputs=[SkillOutput("y", "str", "output")],
        execute=_noop,
        governance_level="ALLOW",
        routing_conditions=["test"],
        memory_updates=["record"],
        observability_hooks=["log"],
    )
    defaults.update(overrides)
    return SkillSchema(**defaults)


def test_valid_skill_passes() -> None:
    """A well-formed skill passes validation without errors."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill())
    assert result.valid is True
    assert len(result.errors) == 0


def test_missing_name_fails() -> None:
    """A skill without a name is rejected."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill(name=""))
    assert result.valid is False
    assert any("name" in e.lower() for e in result.errors)


def test_missing_governance_level_fails() -> None:
    """A skill with an invalid governance declaration is rejected."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill(governance_level="INVALID"))
    assert result.valid is False
    assert any("governance" in e.lower() for e in result.errors)


def test_missing_inputs_fails() -> None:
    """A skill without inputs is rejected."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill(inputs=[]))
    assert result.valid is False
    assert any("input" in e.lower() for e in result.errors)


def test_missing_outputs_fails() -> None:
    """A skill without outputs is rejected."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill(outputs=[]))
    assert result.valid is False
    assert any("output" in e.lower() for e in result.errors)


def test_invalid_version_warned() -> None:
    """A non-semver version is flagged as a warning but not an error."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill(version="v2"))
    assert result.valid is True
    assert any("semver" in w.lower() for w in result.warnings)


def test_missing_routing_conditions_warned() -> None:
    """A skill without routing_conditions receives a warning."""
    validator = SkillValidator()
    result = validator.validate_schema(_valid_skill(routing_conditions=[]))
    assert result.valid is True
    assert any("routing" in w.lower() for w in result.warnings)


def test_validate_execution_success() -> None:
    """Execution validation passes for valid results."""
    validator = SkillValidator()
    skill = _valid_skill()
    result = SkillResult(
        success=True,
        outputs={"y": "value"},
        confidence=0.9,
        trace_id="abc123",
        execution_time_ms=10.0,
    )
    validation = validator.validate_execution(skill, result)
    assert validation.valid is True


def test_validate_execution_missing_trace_id() -> None:
    """Execution result without trace_id fails."""
    validator = SkillValidator()
    skill = _valid_skill()
    result = SkillResult(
        success=True,
        outputs={"y": "value"},
        trace_id="",
        execution_time_ms=10.0,
    )
    validation = validator.validate_execution(skill, result)
    assert validation.valid is False
    assert any("trace_id" in e for e in validation.errors)
