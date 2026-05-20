"""Tests for skills.core.skill_registry — Registration, discovery, persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillResult,
    SkillSchema,
)
from skills.core.skill_registry import SkillRegistry


def _make_skill(
    name: str,
    routing: list[str] | None = None,
    tags: list[str] | None = None,
    governance: str = "ALLOW",
) -> SkillSchema:
    def _exec(ctx: SkillContext) -> SkillResult:
        return SkillResult(success=True, outputs={"result": name})

    return SkillSchema(
        name=name,
        version="1.0.0",
        description=f"Skill: {name}",
        inputs=[SkillInput("task_description", "str", True, "task")],
        outputs=[SkillOutput("result", "str", "output")],
        execute=_exec,
        routing_conditions=routing or [],
        memory_updates=["record_execution"],
        governance_level=governance,
        observability_hooks=["log_execution"],
        metadata=SkillMetadata(tags=tags or []),
    )


def test_register_skill(tmp_dir: Path) -> None:
    """Register a skill and retrieve it by skill_id."""
    registry = SkillRegistry(store_path=tmp_dir / "reg.jsonl")
    skill = _make_skill("my-skill", tags=["alpha"])
    sid = registry.register(skill)

    assert sid == skill.skill_id
    retrieved = registry.get(sid)
    assert retrieved is not None
    assert retrieved.name == "my-skill"


def test_deregister_skill(tmp_dir: Path) -> None:
    """Deregister a skill and verify it cannot be found."""
    registry = SkillRegistry(store_path=tmp_dir / "reg.jsonl")
    skill = _make_skill("removable")
    sid = registry.register(skill)
    assert registry.get(sid) is not None

    result = registry.deregister(sid)
    assert result is True
    assert registry.get(sid) is None

    assert registry.deregister("nonexistent-id") is False


def test_find_best_returns_ranked(tmp_dir: Path) -> None:
    """find_best returns skills sorted by confidence, highest first."""
    registry = SkillRegistry(store_path=tmp_dir / "reg.jsonl")

    low = _make_skill("low-match", routing=["anomaly"])
    high = _make_skill("high-match", routing=["anomaly", "explain"])
    registry.register(low)
    registry.register(high)

    results = registry.find_best("explain the anomaly")
    assert len(results) >= 1
    names = [s.name for s, _ in results]
    assert "high-match" in names

    if len(results) >= 2:
        assert results[0][1] >= results[1][1]


def test_find_by_tag(tmp_dir: Path) -> None:
    """Tag-based filtering returns correct skills."""
    registry = SkillRegistry(store_path=tmp_dir / "reg.jsonl")
    s1 = _make_skill("tagged-a", tags=["system", "network"])
    s2 = _make_skill("tagged-b", tags=["memory"])
    registry.register(s1)
    registry.register(s2)

    found = registry.find_by_tag(["network"])
    assert len(found) == 1
    assert found[0].name == "tagged-a"

    found_both = registry.find_by_tag(["system", "memory"])
    names = {s.name for s in found_both}
    assert "tagged-a" in names
    assert "tagged-b" in names


def test_duplicate_registration(tmp_dir: Path) -> None:
    """Registering the same skill_id twice replaces the entry gracefully."""
    registry = SkillRegistry(store_path=tmp_dir / "reg.jsonl")
    skill = _make_skill("dup-skill")
    sid1 = registry.register(skill)
    sid2 = registry.register(skill)
    assert sid1 == sid2
    assert len(registry.list_all()) == 1


def test_registry_persistence(tmp_dir: Path) -> None:
    """save / load roundtrip preserves skill metadata."""
    path = tmp_dir / "persist.jsonl"
    registry = SkillRegistry(store_path=path)
    s1 = _make_skill("persist-a", tags=["x"])
    s2 = _make_skill("persist-b", tags=["y"])
    registry.register(s1)
    registry.register(s2)

    saved = registry.save()
    assert saved == 2

    registry2 = SkillRegistry(store_path=path)
    loaded = registry2.load()
    assert loaded == 2


def test_status_report(tmp_dir: Path) -> None:
    """status_report returns valid summary."""
    registry = SkillRegistry(store_path=tmp_dir / "reg.jsonl")
    registry.register(_make_skill("a", tags=["t1"]))
    registry.register(_make_skill("b", tags=["t2"], governance="REVIEW_REQUIRED"))

    report = registry.status_report()
    assert report["total_skills"] == 2
    assert report["enabled"] == 2
    assert "ALLOW" in report["by_governance"]
