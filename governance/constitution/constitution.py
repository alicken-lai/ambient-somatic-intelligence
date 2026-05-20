"""Frozen constitution — rules loaded once and sealed; no runtime mutation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.constitution.constitutional_lock import ConstitutionalLock, ConstitutionalLockError
from governance.constitution.constitutional_rule import ConstitutionalRule
from governance.constitution.epistemic_limit import EPISTEMIC_LIMIT_RULE
from governance.constitution.forecast_boundary import FORECAST_BOUNDARY_RULE
from governance.constitution.guardian_supremacy import GUARDIAN_SUPREMACY_RULE
from governance.constitution.replay_boundary import REPLAY_BOUNDARY_RULE
from governance.constitution.self_modification_guard import SELF_MODIFICATION_RULE


def _default_rules() -> tuple[ConstitutionalRule, ...]:
    return (
        GUARDIAN_SUPREMACY_RULE,
        EPISTEMIC_LIMIT_RULE,
        REPLAY_BOUNDARY_RULE,
        FORECAST_BOUNDARY_RULE,
        SELF_MODIFICATION_RULE,
        ConstitutionalRule(
            rule_id="no_autonomous_execution",
            name="No Autonomous Execution",
            description="Cognitive governance is advisory; it cannot execute side effects.",
            severity="block",
        ),
        ConstitutionalRule(
            rule_id="no_recursive_governance",
            name="No Recursive Governance",
            description="Governance cannot recurse on itself or form constitutional loops.",
            severity="block",
        ),
    )


@dataclass
class Constitution:
    """Immutable constitutional rule set (v0.6.1)."""

    version: str = "0.6.1"
    rules: tuple[ConstitutionalRule, ...] = field(default_factory=_default_rules)
    _lock: ConstitutionalLock = field(default_factory=ConstitutionalLock, repr=False)
    _sealed: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    def seal(self) -> None:
        """Seal constitution — rules become immutable for process lifetime."""
        if self._sealed:
            return
        self._lock.seal()
        object.__setattr__(self, "_sealed", True)

    @property
    def sealed(self) -> bool:
        return self._sealed

    def rule_ids(self) -> frozenset[str]:
        return frozenset(r.rule_id for r in self.rules)

    def get_rule(self, rule_id: str) -> ConstitutionalRule | None:
        for r in self.rules:
            if r.rule_id == rule_id:
                return r
        return None

    def attempt_add_rule(self, rule: ConstitutionalRule) -> None:
        """Always forbidden after seal — constitutional mutation blocked."""
        self._lock.assert_mutable("add_rule")
        raise ConstitutionalLockError("constitutional_rules_are_frozen_at_load")

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "sealed": self._sealed,
            "rule_count": len(self.rules),
            "rules": [r.to_dict() for r in self.rules],
        }


_DEFAULT_CONSTITUTION: Constitution | None = None


def load_constitution(*, seal: bool = True) -> Constitution:
    """Load and optionally seal the process-default frozen constitution."""
    global _DEFAULT_CONSTITUTION
    if _DEFAULT_CONSTITUTION is None:
        c = Constitution()
        if seal:
            c.seal()
        _DEFAULT_CONSTITUTION = c
    return _DEFAULT_CONSTITUTION
