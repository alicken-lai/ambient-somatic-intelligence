"""Self-modification guard metrics — runtime constitutional mutation attempts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.constitution.constitutional_guard import ConstitutionalContext, ConstitutionalGuard


@dataclass
class SelfModificationMetrics:
    mutation_block_rate: float = 1.0
    mutation_attempts_blocked: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutation_block_rate": round(self.mutation_block_rate, 4),
            "mutation_attempts_blocked": self.mutation_attempts_blocked,
        }


def collect_self_modification_metrics() -> SelfModificationMetrics:
    guard = ConstitutionalGuard()
    attempts = [
        ConstitutionalContext(),
        ConstitutionalContext(mutation_attempt=True),
        ConstitutionalContext(metadata={"mutate_constitution": True}),
    ]
    blocked = sum(1 for c in attempts if not guard.evaluate(c).compliant)
    n = len(attempts)
    return SelfModificationMetrics(
        mutation_block_rate=blocked / n if n else 1.0,
        mutation_attempts_blocked=blocked,
    )
