"""
Salience competition — fair allocation of finite attention across targets.

Targets compete for a finite attention budget.  ``compete_with_report`` admits
the highest-salience targets greedily until the budget is exhausted (always
admitting at least the single strongest), and reports a fairness index over the
full field of contenders.

Fairness is measured with Jain's fairness index::

    J(x) = (sum x_i)^2 / (n * sum x_i^2)

which lies in ``(1/n, 1]`` — 1.0 when every contender has equal salience and
lower as the distribution becomes more skewed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from attention.core.attention_target import AttentionTarget


def jain_fairness(scores: list[float]) -> float:
    """Jain's fairness index over *scores* (1.0 == perfectly equal)."""
    positive = [max(0.0, s) for s in scores]
    denom = len(positive) * sum(s * s for s in positive)
    if denom <= 0.0:
        return 1.0
    return (sum(positive) ** 2) / denom


@dataclass
class CompetitionReport:
    """Outcome of a salience competition round."""

    winners: list[AttentionTarget] = field(default_factory=list)
    losers: list[AttentionTarget] = field(default_factory=list)
    fairness_score: float = 1.0
    admitted_salience: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "winners": [t.target_id for t in self.winners],
            "losers": [t.target_id for t in self.losers],
            "fairness_score": round(self.fairness_score, 4),
            "admitted_salience": round(self.admitted_salience, 4),
        }


class SalienceCompetition:
    """Admits competing targets under a finite attention budget."""

    def __init__(self, budget: float = 1.0) -> None:
        self.budget = max(0.0, float(budget))

    def compete_with_report(
        self,
        contenders: list[tuple[AttentionTarget, float]],
    ) -> CompetitionReport:
        """Run a competition round and return a :class:`CompetitionReport`."""
        if not contenders:
            return CompetitionReport()

        ranked = sorted(contenders, key=lambda pair: pair[1], reverse=True)
        winners: list[AttentionTarget] = []
        losers: list[AttentionTarget] = []
        spent = 0.0

        for target, score in ranked:
            if not winners or spent + score <= self.budget:
                winners.append(target)
                spent += score
            else:
                losers.append(target)

        return CompetitionReport(
            winners=winners,
            losers=losers,
            fairness_score=jain_fairness([s for _, s in ranked]),
            admitted_salience=spent,
        )
