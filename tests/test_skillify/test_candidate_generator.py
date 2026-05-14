"""Tests for agents.skillify.skill_candidate_generator — Candidate generation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents.skillify.pattern_miner import WorkflowPattern
from agents.skillify.workflow_cluster import WorkflowCluster, WorkflowClusterGroup
from agents.skillify.skill_candidate_generator import SkillCandidateGenerator


def _make_pattern(
    pattern_id: str,
    workflow_type: str = "anomaly_detection",
    success_rate: float = 0.9,
    occurrence_count: int = 10,
) -> WorkflowPattern:
    now = datetime.now(timezone.utc)
    return WorkflowPattern(
        pattern_id=pattern_id,
        workflow_type=workflow_type,
        canonical_steps=["collect", "evaluate", "report"],
        occurrence_count=occurrence_count,
        success_rate=success_rate,
        avg_duration_ms=500.0,
        input_schema={"description": "str", "threshold": "float"},
        output_schema={"status": "str", "score": "float"},
        variation_score=0.1,
        governance_requirements=[],
        first_seen=now,
        last_seen=now,
    )


def _make_cluster(patterns: list[WorkflowPattern]) -> WorkflowClusterGroup:
    """Build a cluster group from patterns using the actual clusterer."""
    clusterer = WorkflowCluster()
    groups = clusterer.cluster(patterns, threshold=0.0)
    if groups:
        return groups[0]
    return WorkflowClusterGroup(
        cluster_id="test-cluster",
        patterns=patterns,
        representative=patterns[0],
        similarity_matrix={},
        skill_potential=0.8,
    )


def test_generate_candidate(tmp_dir: Path) -> None:
    """Generate a SkillCandidate from a cluster."""
    patterns = [
        _make_pattern("g1"),
        _make_pattern("g2"),
    ]
    cluster = _make_cluster(patterns)

    gen = SkillCandidateGenerator(candidates_path=tmp_dir / "candidates.jsonl")
    candidate = gen.generate(cluster)

    assert candidate.proposed_name
    assert candidate.proposed_version == "0.1.0"
    assert candidate.description
    assert len(candidate.proposed_inputs) >= 1
    assert len(candidate.proposed_outputs) >= 1
    assert candidate.source_patterns


def test_candidate_status_draft(tmp_dir: Path) -> None:
    """Generated candidates start as 'draft' status."""
    patterns = [_make_pattern("d1"), _make_pattern("d2")]
    cluster = _make_cluster(patterns)

    gen = SkillCandidateGenerator(candidates_path=tmp_dir / "candidates.jsonl")
    candidate = gen.generate(cluster)

    assert candidate.status == "draft"


def test_candidate_evidence(tmp_dir: Path) -> None:
    """Candidate carries evidence from source patterns."""
    patterns = [
        _make_pattern("e1", success_rate=0.95, occurrence_count=15),
        _make_pattern("e2", success_rate=0.88, occurrence_count=12),
    ]
    cluster = _make_cluster(patterns)

    gen = SkillCandidateGenerator(candidates_path=tmp_dir / "candidates.jsonl")
    candidate = gen.generate(cluster)

    assert candidate.evidence["occurrence_count"] > 0
    assert candidate.evidence["success_rate"] > 0
    assert candidate.evidence["pattern_count"] >= 2
