"""
Cognitive Constitutional Layer (v0.6.1) — frozen rules evaluated before arbitration.

Rules are immutable at load; runtime cannot mutate the constitution.
"""

from governance.constitution.constitution import Constitution, load_constitution
from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard
from governance.constitution.constitutional_lock import ConstitutionalLock, ConstitutionalLockError
from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.constitutional_violation import ConstitutionalVerdict, ConstitutionalViolation

__all__ = [
    "Constitution",
    "ConstitutionalContext",
    "ConstitutionalGuard",
    "ConstitutionalLock",
    "ConstitutionalLockError",
    "ConstitutionalRule",
    "ConstitutionalVerdict",
    "ConstitutionalViolation",
    "load_constitution",
]
