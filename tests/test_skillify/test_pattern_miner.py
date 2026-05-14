"""Tests for agents.skillify.pattern_miner — Pattern mining, min support."""

from __future__ import annotations

from agents.skillify.workflow_observer import WorkflowEvent, WorkflowStep
from agents.skillify.pattern_miner import SkillifyPatternMiner


def _make_event(
    workflow_type: str = "anomaly_detection",
    steps: list[str] | None = None,
    success: bool = True,
    duration_ms: float = 500.0,
) -> WorkflowEvent:
    step_names = steps or ["collect", "evaluate", "report"]
    return WorkflowEvent.create(
        workflow_type=workflow_type,
        steps=[
            WorkflowStep(s, "mod", "fn", duration_ms / len(step_names), True)
            for s in step_names
        ],
        inputs={"description": f"task for {workflow_type}"},
        outputs={"status": "done"},
        success=success,
        duration_ms=duration_ms,
    )


def test_mine_patterns() -> None:
    """Find recurring patterns from observations."""
    miner = SkillifyPatternMiner()
    events = [_make_event() for _ in range(5)]

    patterns = miner.mine(events, min_support=3)
    assert len(patterns) >= 1

    p = patterns[0]
    assert p.workflow_type == "anomaly_detection"
    assert p.occurrence_count == 5
    assert p.success_rate == 1.0
    assert p.canonical_steps == ["collect", "evaluate", "report"]


def test_min_support() -> None:
    """Patterns below min_support threshold are excluded."""
    miner = SkillifyPatternMiner()
    events = [
        _make_event("common") for _ in range(5)
    ] + [
        _make_event("rare") for _ in range(2)
    ]

    patterns = miner.mine(events, min_support=3)
    types = {p.workflow_type for p in patterns}
    assert "common" in types
    assert "rare" not in types


def test_variation_score() -> None:
    """Patterns with mixed step sequences have higher variation."""
    miner = SkillifyPatternMiner()

    events_uniform = [
        _make_event("uniform", steps=["a", "b", "c"]) for _ in range(5)
    ]
    events_varied = [
        _make_event("varied", steps=["a", "b", "c"]),
        _make_event("varied", steps=["a", "c", "b"]),
        _make_event("varied", steps=["b", "a", "c"]),
        _make_event("varied", steps=["a", "b", "c"]),
        _make_event("varied", steps=["c", "b", "a"]),
    ]

    p_uniform = miner.mine(events_uniform, min_support=3)[0]
    p_varied = miner.mine(events_varied, min_support=3)[0]

    assert p_uniform.variation_score <= p_varied.variation_score


def test_empty_observations() -> None:
    """Mining empty observations returns no patterns."""
    miner = SkillifyPatternMiner()
    assert miner.mine([], min_support=1) == []
