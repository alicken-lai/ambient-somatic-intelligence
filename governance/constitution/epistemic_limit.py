"""Epistemic limits — no certainty claims; confidence capped probabilistically."""

from __future__ import annotations

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.constitutional_violation import ConstitutionalViolation
from observability.v04.metric_normalizer import clamp01

EPISTEMIC_LIMIT_RULE = ConstitutionalRule(
    rule_id="epistemic_limit",
    name="Epistemic Limit",
    description="Cognition remains probabilistic; certainty (1.0) is constitutionally forbidden.",
    severity="block",
)

CERTAINTY_EPSILON = 1e-6


def check_epistemic_limit(
    *,
    raw_confidence: float,
    certainty_claim: bool = False,
    deterministic_authority: bool = False,
) -> ConstitutionalViolation | None:
    conf = clamp01(raw_confidence)
    if certainty_claim or deterministic_authority:
        return ConstitutionalViolation(
            rule_id=EPISTEMIC_LIMIT_RULE.rule_id,
            message="deterministic_authority_or_certainty_claim_forbidden",
            severity="block",
        )
    if conf >= ABSOLUTE_MAX_CONFIDENCE - CERTAINTY_EPSILON and conf >= 0.999:
        return ConstitutionalViolation(
            rule_id=EPISTEMIC_LIMIT_RULE.rule_id,
            message="confidence_at_certainty_boundary",
            severity="block",
        )
    return None
