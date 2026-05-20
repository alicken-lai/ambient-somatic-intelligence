"""Guardian supremacy — constitutional rule; Guardian policy cannot be weakened."""

from __future__ import annotations

from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.constitutional_violation import ConstitutionalViolation

GUARDIAN_SUPREMACY_RULE = ConstitutionalRule(
    rule_id="guardian_supremacy",
    name="Guardian Supremacy",
    description="Side effects require Guardian; agents must not bypass or weaken Guardian.",
    severity="block",
)

FORBIDDEN_GUARDIAN_ROUTES = frozenset({
    "guardian_bypass",
    "weaken_guardian",
    "skip_guardian_check",
    "autonomous_side_effect",
})


def check_guardian_supremacy(
    *,
    route_name: str = "",
    guardian_bypass_attempt: bool = False,
    weaken_guardian: bool = False,
) -> ConstitutionalViolation | None:
    if guardian_bypass_attempt or weaken_guardian:
        return ConstitutionalViolation(
            rule_id=GUARDIAN_SUPREMACY_RULE.rule_id,
            message="attempted_guardian_weakening_or_bypass",
            severity="block",
        )
    if route_name in FORBIDDEN_GUARDIAN_ROUTES:
        return ConstitutionalViolation(
            rule_id=GUARDIAN_SUPREMACY_RULE.rule_id,
            message=f"forbidden_route:{route_name}",
            severity="block",
        )
    return None
