"""Tests for skills.core.skill_schema — SkillSchema creation, validation, serialization."""

from __future__ import annotations

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillResult,
    SkillSchema,
)


def test_create_valid_skill(sample_skill_schema: SkillSchema) -> None:
    """Create a SkillSchema with all required fields and verify them."""
    skill = sample_skill_schema
    assert skill.name == "test-skill"
    assert skill.version == "1.0.0"
    assert skill.description
    assert len(skill.inputs) == 1
    assert len(skill.outputs) == 1
    assert callable(skill.execute)
    assert skill.governance_level == "ALLOW"
    assert skill.enabled is True


def test_skill_metadata_auto_generated() -> None:
    """skill_id and created_at are auto-populated when not provided."""

    def _noop(ctx: SkillContext) -> SkillResult:
        return SkillResult(success=True)

    skill = SkillSchema(
        name="auto-meta",
        version="0.1.0",
        description="Test auto metadata",
        inputs=[SkillInput("x", "int", True, "input")],
        outputs=[SkillOutput("y", "int", "output")],
        execute=_noop,
    )
    assert skill.skill_id.startswith("skill-")
    assert len(skill.skill_id) > 6
    assert skill.created_at  # non-empty ISO timestamp


def test_skill_serialization_roundtrip(sample_skill_schema: SkillSchema) -> None:
    """to_dict → from_dict preserves all serializable fields."""
    d = sample_skill_schema.to_dict()

    assert d["name"] == "test-skill"
    assert d["version"] == "1.0.0"
    assert d["skill_id"] == sample_skill_schema.skill_id
    assert d["enabled"] is True
    assert d["governance_level"] == "ALLOW"
    assert d["created_at"] == sample_skill_schema.created_at

    assert len(d["inputs"]) == 1
    assert d["inputs"][0]["name"] == "task_description"
    assert len(d["outputs"]) == 1
    assert d["outputs"][0]["name"] == "answer"

    assert d["routing_conditions"] == ["test", "unit"]
    assert d["memory_updates"] == ["record_execution"]
    assert d["metadata"]["tags"] == ["testing", "unit"]


def test_skill_matches_task(sample_skill_schema: SkillSchema) -> None:
    """routing_conditions correctly match task descriptions."""
    score_match = sample_skill_schema.matches_task("run the unit test suite")
    assert score_match > 0.0

    score_none = sample_skill_schema.matches_task("deploy production server")
    assert score_none == 0.0


def test_skill_matches_task_disabled() -> None:
    """A disabled skill returns 0.0 for any task."""

    def _noop(ctx: SkillContext) -> SkillResult:
        return SkillResult(success=True)

    skill = SkillSchema(
        name="disabled",
        version="1.0.0",
        description="disabled skill",
        inputs=[SkillInput("x", "str", True, "input")],
        outputs=[SkillOutput("y", "str", "output")],
        execute=_noop,
        routing_conditions=["test"],
        enabled=False,
    )
    assert skill.matches_task("test something") == 0.0


def test_skill_run_success(sample_skill_schema: SkillSchema) -> None:
    """SkillSchema.run() returns a result with timing and trace_id."""
    ctx = SkillContext(task_description="unit test")
    result = sample_skill_schema.run(ctx)
    assert result.success is True
    assert result.outputs == {"answer": "ok"}
    assert result.execution_time_ms >= 0
    assert result.trace_id == ctx.trace_id


def test_skill_run_exception() -> None:
    """SkillSchema.run() captures exceptions gracefully."""

    def _fail(ctx: SkillContext) -> SkillResult:
        raise RuntimeError("boom")

    skill = SkillSchema(
        name="failing",
        version="1.0.0",
        description="always fails",
        inputs=[SkillInput("x", "str", True, "input")],
        outputs=[SkillOutput("y", "str", "output")],
        execute=_fail,
    )
    ctx = SkillContext(task_description="will fail")
    result = skill.run(ctx)
    assert result.success is False
    assert "boom" in result.error
    assert result.trace_id == ctx.trace_id
