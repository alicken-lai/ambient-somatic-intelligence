"""Guardian supremacy constitutional metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


@dataclass
class GuardianSupremacyMetrics:
    supremacy_preserved_rate: float = 1.0
    bypass_attempts_blocked: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "supremacy_preserved_rate": round(self.supremacy_preserved_rate, 4),
            "bypass_attempts_blocked": self.bypass_attempts_blocked,
        }


def collect_guardian_supremacy_metrics() -> GuardianSupremacyMetrics:
    guard = ConstitutionalGuard()
    bypass_attempts = [
        ConstitutionalContext(route_name="guardian_bypass", guardian_bypass_attempt=True),
        ConstitutionalContext(weaken_guardian=True),
        ConstitutionalContext(route_name="skip_guardian_check"),
    ]
    blocked = sum(1 for c in bypass_attempts if not guard.evaluate(c).compliant)
    n = len(bypass_attempts) or 1
    return GuardianSupremacyMetrics(
        supremacy_preserved_rate=blocked / n,
        bypass_attempts_blocked=blocked,
    )
