"""Tests for agents.skillify.skill_registration_pipeline — Full pipeline, governance."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from agents.skillify.skill_candidate_generator import SkillCandidate
from agents.skillify.skill_registration_pipeline import SkillRegistrationPipeline


def _make_candidate(
    name: str = "auto_test_skill",
    success_rate: float = 0.9,
    occurrence_count: int = 10,
) -> SkillCandidate:
    return SkillCandidate(
        candidate_id="cand-pipeline-001",
        proposed_name=name,
        proposed_version="0.1.0",
        description="Pipeline test candidate",
        proposed_inputs=[{"name": "description", "type": "str", "required": True}],
        proposed_outputs=[{"name": "result", "type": "str"}],
        confidence_range=(0.5, 0.9),
        routing_conditions=["test"],
        memory_updates=["record"],
        governance_level="ALLOW",
        observability_hooks=["log"],
        source_patterns=["wp-001"],
        evidence={
            "occurrence_count": occurrence_count,
            "success_rate": success_rate,
            "pattern_count": 2,
            "skill_potential": 0.8,
        },
        status="draft",
        created_at=datetime.now(timezone.utc),
    )


def test_propose_requires_governance(tmp_dir: Path) -> None:
    """propose() creates a governance review ticket."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    candidate = _make_candidate()
    result = pipeline.propose(candidate)

    assert result.governance_ticket.startswith("GOV-")
    assert result.status in ("pending_review", "rejected")
    assert result.proposal_id.startswith("prop-")


def test_approve_then_register(tmp_dir: Path) -> None:
    """Full pipeline: propose → approve → register."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    candidate = _make_candidate()
    proposal = pipeline.propose(candidate)

    assert proposal.status == "pending_review"

    approval = pipeline.approve(proposal.proposal_id, reviewer="admin", notes="LGTM")
    assert approval.status == "approved"

    reg = pipeline.register(proposal.proposal_id)
    assert reg.skill_id.startswith("skill-")
    assert reg.reversible is True


def test_register_without_approval_fails(tmp_dir: Path) -> None:
    """Can't register a proposal that hasn't been approved."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    candidate = _make_candidate()
    proposal = pipeline.propose(candidate)

    with pytest.raises(ValueError, match="approved"):
        pipeline.register(proposal.proposal_id)


def test_rollback(tmp_dir: Path) -> None:
    """Registered skill can be rolled back."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    candidate = _make_candidate()
    proposal = pipeline.propose(candidate)
    pipeline.approve(proposal.proposal_id, reviewer="admin")
    reg = pipeline.register(proposal.proposal_id)

    success = pipeline.rollback(reg.skill_id)
    assert success is True


def test_reject_candidate(tmp_dir: Path) -> None:
    """Rejected candidates cannot be registered."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    candidate = _make_candidate()
    proposal = pipeline.propose(candidate)

    pipeline.reject(proposal.proposal_id, reason="Not needed")

    with pytest.raises(ValueError, match="rejected"):
        pipeline.register(proposal.proposal_id)


def test_propose_invalid_candidate_rejected(tmp_dir: Path) -> None:
    """An invalid candidate is auto-rejected during proposal."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    bad_candidate = _make_candidate(name="", success_rate=0.1, occurrence_count=1)
    result = pipeline.propose(bad_candidate)

    assert result.status == "rejected"


def test_list_pending(tmp_dir: Path) -> None:
    """list_pending returns only pending proposals."""
    pipeline = SkillRegistrationPipeline(state_path=tmp_dir / "state.jsonl")
    c1 = _make_candidate("skill_a")
    c2 = _make_candidate("skill_b")

    pipeline.propose(c1)
    pipeline.propose(c2)

    pending = pipeline.list_pending()
    assert len(pending) == 2
