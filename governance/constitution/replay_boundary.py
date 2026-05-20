"""Replay boundary — read-only replay blend; no replay-driven side effects."""

from __future__ import annotations

from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.constitutional_violation import ConstitutionalViolation
from observability.v04.metric_normalizer import clamp01

REPLAY_BOUNDARY_RULE = ConstitutionalRule(
    rule_id="replay_boundary",
    name="Replay Boundary",
    description="Replay hints are advisory read-only blends; replay cannot authorize execution.",
    severity="block",
)

MAX_REPLAY_HINT = 0.85


def check_replay_boundary(
    *,
    replay_hint: float = 0.0,
    replay_executes: bool = False,
    replay_write: bool = False,
) -> ConstitutionalViolation | None:
    if replay_executes or replay_write:
        return ConstitutionalViolation(
            rule_id=REPLAY_BOUNDARY_RULE.rule_id,
            message="replay_must_remain_read_only",
            severity="block",
        )
    hint = clamp01(replay_hint)
    if hint > MAX_REPLAY_HINT:
        return ConstitutionalViolation(
            rule_id=REPLAY_BOUNDARY_RULE.rule_id,
            message=f"replay_hint_exceeds_boundary:{hint:.3f}",
            severity="block",
        )
    return None
