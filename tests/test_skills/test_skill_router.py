"""Tests for skills.core.skill_router — Routing decisions, governance, fallback."""

from __future__ import annotations

from pathlib import Path

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillOutput,
    SkillResult,
    SkillSchema,
)
from skills.core.skill_registry import SkillRegistry
from skills.core.skill_router import SkillRouter


def _make_skill(
    name: str,
    routing: list[str],
    governance: str = "ALLOW",
    fail: bool = False,
) -> SkillSchema:
    def _exec(ctx: SkillContext) -> SkillResult:
        if fail:
            return SkillResult(success=False, error=f"{name} failed")
        return SkillResult(success=True, outputs={"from": name}, confidence=0.9)

    return SkillSchema(
        name=name,
        version="1.0.0",
        description=f"Skill: {name}",
        inputs=[SkillInput("task_description", "str", True, "task")],
        outputs=[SkillOutput("result", "str", "output")],
        execute=_exec,
        routing_conditions=routing,
        memory_updates=["record"],
        governance_level=governance,
        observability_hooks=["log"],
    )


def test_route_selects_best_skill(tmp_dir: Path) -> None:
    """Routing picks the highest-confidence skill."""
    registry = SkillRegistry(store_path=tmp_dir / "r.jsonl")
    registry.register(_make_skill("broad", routing=["anomaly"]))
    registry.register(_make_skill("specific", routing=["anomaly", "explain", "detail"]))

    router = SkillRouter(registry)
    decision = router.route("explain the anomaly in detail")

    assert decision.selected_skill is not None
    assert decision.confidence > 0


def test_route_governance_check(tmp_dir: Path) -> None:
    """Skills requiring REVIEW_REQUIRED flag governance_check_required."""
    registry = SkillRegistry(store_path=tmp_dir / "r.jsonl")
    registry.register(
        _make_skill("guarded", routing=["deploy"], governance="REVIEW_REQUIRED")
    )

    router = SkillRouter(registry)
    decision = router.route("deploy the update", governance_clearance="ALLOW")

    assert decision.selected_skill is not None
    assert decision.governance_check_required is True


def test_route_no_match(tmp_dir: Path) -> None:
    """Returns None when no skill matches the task."""
    registry = SkillRegistry(store_path=tmp_dir / "r.jsonl")
    registry.register(_make_skill("niche", routing=["quantum-flux"]))

    router = SkillRouter(registry)
    decision = router.route("make coffee")

    assert decision.selected_skill is None
    assert decision.confidence == 0.0


def test_fallback_chain(tmp_dir: Path) -> None:
    """execute_with_fallback tries alternatives when primary fails."""
    registry = SkillRegistry(store_path=tmp_dir / "r.jsonl")
    registry.register(_make_skill("primary", routing=["fix", "bug"], fail=True))
    registry.register(_make_skill("backup", routing=["fix"]))

    router = SkillRouter(registry)
    decision = router.route("fix the bug")

    assert decision.selected_skill is not None
    ctx = SkillContext(task_description="fix the bug")
    result = router.execute_with_fallback(decision, ctx)

    assert result.success is True
    assert result.outputs.get("from") == "backup"


def test_execute_with_fallback_no_skill(tmp_dir: Path) -> None:
    """execute_with_fallback returns error when no skill selected."""
    registry = SkillRegistry(store_path=tmp_dir / "r.jsonl")
    router = SkillRouter(registry)
    decision = router.route("nonexistent task")

    ctx = SkillContext(task_description="nonexistent task")
    result = router.execute_with_fallback(decision, ctx)
    assert result.success is False
    assert "No skill was selected" in result.error


def test_execute_with_fallback_governance_blocked(tmp_dir: Path) -> None:
    """execute_with_fallback returns error when governance blocks."""
    registry = SkillRegistry(store_path=tmp_dir / "r.jsonl")
    registry.register(
        _make_skill("blocked", routing=["action"], governance="BLOCK_WITHOUT_APPROVAL")
    )

    router = SkillRouter(registry)
    decision = router.route("take action", governance_clearance="ALLOW")

    ctx = SkillContext(task_description="take action")
    result = router.execute_with_fallback(decision, ctx)
    assert result.success is False
    assert "Governance" in result.error
