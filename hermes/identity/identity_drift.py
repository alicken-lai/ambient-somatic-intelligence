"""Identity drift detection."""

from __future__ import annotations

from hermes.identity.identity_models import IdentityProfile


FORBIDDEN_PATTERNS = ("override guardian", "bypass guardian", "modify credentials", "silent governance", "unconstrained agency")
NEGATIONS = ("do not", "not ", "no ", "may not", "cannot", "must not")


def detect_identity_drift(identity: IdentityProfile, statements: list[str]) -> dict[str, object]:
    normalized = [statement.lower() for statement in statements]
    joined = " ".join(normalized)
    conflicts = [
        pattern
        for pattern in FORBIDDEN_PATTERNS
        if any(pattern in statement and not _is_negated(statement, pattern) for statement in normalized)
    ]
    missing_commitments = [item for item in identity.governance_commitments if item.lower() not in joined and "do not" in item.lower()]
    if conflicts:
        return {"drift_detected": True, "severity": "high", "reason": f"conflicts with identity constraints: {', '.join(conflicts)}"}
    if len(missing_commitments) == len(identity.governance_commitments):
        return {"drift_detected": True, "severity": "medium", "reason": "no governance commitments surfaced in current narrative statements"}
    return {"drift_detected": False, "severity": "none", "reason": "no conflict with core identity commitments detected"}


def _is_negated(statement: str, pattern: str) -> bool:
    index = statement.find(pattern)
    if index < 0:
        return False
    prefix = statement[max(0, index - 24):index]
    return any(negation in prefix for negation in NEGATIONS)
