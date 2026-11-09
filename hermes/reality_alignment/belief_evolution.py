"""Belief evolution rules for advisory reality alignment."""

from __future__ import annotations

from hermes.reality_alignment.reality_models import Belief, ChallengeResult


def evolve_belief(belief: Belief, challenges: list[ChallengeResult]) -> Belief:
    related = [item for item in challenges if item.target_id == belief.source_target_id]
    if not related:
        return belief
    successes = sum(1 for item in related if item.passed)
    failures = len(related) - successes
    confidence = belief.confidence
    status = belief.status
    if successes >= 2:
        confidence = min(1.0, confidence + 0.05)
    if failures:
        confidence = max(0.0, confidence - (0.1 * failures))
    if failures >= 2 or (related[-1].reality_score < 45.0):
        status = "retire_recommended"
    elif failures:
        status = "reverify"
    else:
        status = "active"
    return Belief(
        belief_id=belief.belief_id,
        statement=belief.statement,
        confidence=round(confidence, 4),
        reality_score=related[-1].reality_score,
        challenge_count=belief.challenge_count + len(related),
        status=status,
        source_target_id=belief.source_target_id,
    )


def evolve_beliefs(beliefs: dict[str, Belief], challenges: list[ChallengeResult]) -> dict[str, Belief]:
    return {key: evolve_belief(value, challenges) for key, value in beliefs.items()}
