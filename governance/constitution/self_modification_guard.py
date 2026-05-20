"""Self-modification guard — runtime cannot mutate constitutional rules."""

from __future__ import annotations

from typing import Any

from governance.constitution.constitutional_lock import ConstitutionalLock
from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.constitutional_violation import ConstitutionalViolation

SELF_MODIFICATION_RULE = ConstitutionalRule(
    rule_id="self_modification_guard",
    name="Self Modification Guard",
    description="Constitutional rules are frozen at load; runtime mutation is forbidden.",
    severity="block",
)


def check_self_modification(
    lock: ConstitutionalLock,
    *,
    metadata: dict[str, Any] | None = None,
    mutation_attempt: bool = False,
) -> ConstitutionalViolation | None:
    if mutation_attempt:
        return ConstitutionalViolation(
            rule_id=SELF_MODIFICATION_RULE.rule_id,
            message="explicit_constitutional_mutation_attempt",
            severity="block",
        )
    if lock.reject_mutation_payload(metadata):
        return ConstitutionalViolation(
            rule_id=SELF_MODIFICATION_RULE.rule_id,
            message="metadata_constitutional_mutation_forbidden",
            severity="block",
        )
    return None
