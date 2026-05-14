"""Tests for agents.skillify.workflow_cluster — Clustering, similarity."""

from __future__ import annotations

from datetime import datetime, timezone

from agents.skillify.pattern_miner import WorkflowPattern
from agents.skillify.workflow_cluster import WorkflowCluster


def _make_pattern(
    pattern_id: str,
    workflow_type: str = "anomaly_detection",
    steps: list[str] | None = None,
    success_rate: float = 0.9,
    occurrence_count: int = 5,
    input_keys: list[str] | None = None,
    output_keys: list[str] | None = None,
    governance: list[str] | None = None,
) -> WorkflowPattern:
    now = datetime.now(timezone.utc)
    return WorkflowPattern(
        pattern_id=pattern_id,
        workflow_type=workflow_type,
        canonical_steps=steps or ["collect", "evaluate", "report"],
        occurrence_count=occurrence_count,
        success_rate=success_rate,
        avg_duration_ms=500.0,
        input_schema={k: "str" for k in (input_keys or ["description"])},
        output_schema={k: "str" for k in (output_keys or ["status"])},
        variation_score=0.1,
        governance_requirements=governance or [],
        first_seen=now,
        last_seen=now,
    )


def test_cluster_similar() -> None:
    """Similar patterns are grouped into the same cluster."""
    clusterer = WorkflowCluster()

    patterns = [
        _make_pattern("p1", steps=["collect", "evaluate", "report"]),
        _make_pattern("p2", steps=["collect", "evaluate", "report"]),
        _make_pattern("p3", steps=["deploy", "verify", "rollback"]),
    ]

    groups = clusterer.cluster(patterns, threshold=0.5)
    assert len(groups) >= 1

    largest = max(groups, key=lambda g: len(g.patterns))
    assert len(largest.patterns) >= 2


def test_skill_potential() -> None:
    """Clusters get a meaningful skill_potential score (0.0-1.0)."""
    clusterer = WorkflowCluster()

    patterns = [
        _make_pattern("sp1", success_rate=0.95, occurrence_count=10),
        _make_pattern("sp2", success_rate=0.90, occurrence_count=8),
    ]

    groups = clusterer.cluster(patterns, threshold=0.5)
    assert len(groups) >= 1

    for group in groups:
        assert 0.0 <= group.skill_potential <= 1.0
        assert group.representative is not None


def test_empty_patterns() -> None:
    """Clustering empty list returns no groups."""
    clusterer = WorkflowCluster()
    assert clusterer.cluster([]) == []


def test_single_pattern() -> None:
    """A single pattern forms its own group."""
    clusterer = WorkflowCluster()
    patterns = [_make_pattern("solo")]
    groups = clusterer.cluster(patterns, threshold=0.5)
    assert len(groups) == 1
    assert groups[0].representative.pattern_id == "solo"
