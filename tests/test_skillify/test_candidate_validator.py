"""Tests for agents.skillify.skill_candidate_validator — Validation rules, rejection."""

from __future__ import annotations

from datetime import datetime, timezone

from agents.skillify.skill_candidate_generator import SkillCandidate
from agents.skillify.skill_candidate_validator import SkillCandidateValidator


def _make_candidate(
    name: str = "auto_anomaly_detection",
    version: str = "0.1.0",
    description: str = "Auto-generated skill",
    inputs: list[dict] | None = None,
    outputs: list[dict] | None = None,
    governance: str = "ALLOW",
    occurrence_count: int = 10,
    success_rate: float = 0.9,
    skill_potential: float = 0.8,
) -> SkillCandidate:
    return SkillCandidate(
        candidate_id="cand-test-001",
        proposed_name=name,
        proposed_version=version,
        description=description,
        proposed_inputs=inputs if inputs is not None else [{"name": "description", "type": "str", "required": True}],
        proposed_outputs=outputs if outputs is not None else [{"name": "status", "type": "str"}],
        confidence_range=(0.5, 0.9),
        routing_conditions=["anomaly"],
        memory_updates=["record_execution"],
        governance_level=governance,
        observability_hooks=["log"],
        source_patterns=["wp-001"],
        evidence={
            "occurrence_count": occurrence_count,
            "success_rate": success_rate,
            "pattern_count": 2,
            "skill_potential": skill_potential,
        },
        status="draft",
        created_at=datetime.now(timezone.utc),
    )


def test_valid_candidate_passes() -> None:
    """A well-formed candidate passes validation."""
    validator = SkillCandidateValidator()
    result = validator.validate(_make_candidate())
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.quality_score > 0


def test_low_success_rate_fails() -> None:
    """Candidate with <70% success rate is rejected."""
    validator = SkillCandidateValidator(min_success_rate=0.7)
    result = validator.validate(_make_candidate(success_rate=0.5))
    assert result.is_valid is False
    assert any("success rate" in e.lower() for e in result.errors)


def test_missing_name_fails() -> None:
    """Candidate without a name is rejected."""
    validator = SkillCandidateValidator()
    result = validator.validate(_make_candidate(name=""))
    assert result.is_valid is False
    assert any("name" in e.lower() for e in result.errors)


def test_missing_inputs_fails() -> None:
    """Candidate without inputs is rejected."""
    validator = SkillCandidateValidator()
    result = validator.validate(_make_candidate(inputs=[]))
    assert result.is_valid is False
    assert any("input" in e.lower() for e in result.errors)


def test_insufficient_support_fails() -> None:
    """Candidate with too few occurrences is rejected."""
    validator = SkillCandidateValidator(min_support=5)
    result = validator.validate(_make_candidate(occurrence_count=2))
    assert result.is_valid is False
    assert any("support" in e.lower() for e in result.errors)


def test_duplicate_detection() -> None:
    """Candidate name too similar to existing skill is flagged."""
    validator = SkillCandidateValidator(name_similarity_threshold=0.85)
    result = validator.validate(
        _make_candidate(name="auto_anomaly_detection"),
        existing_skill_names=["auto_anomaly_detection_v2"],
    )
    assert result.is_valid is False
    assert any("duplicate" in e.lower() for e in result.errors)


def test_quality_score_zero_on_errors() -> None:
    """Quality score is 0.0 when there are errors."""
    validator = SkillCandidateValidator()
    result = validator.validate(_make_candidate(name="", inputs=[]))
    assert result.quality_score == 0.0
