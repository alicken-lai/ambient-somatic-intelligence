"""
Retrieval Utility Scorer — Score and rank retrieval results by utility.

Goes beyond raw relevance scoring by incorporating multiple dimensions:
  - Relevance: semantic similarity from the retriever
  - Recency: newer information preferred
  - Agent alignment: does the content match the agent's domain?
  - Cost efficiency: utility per token
  - Novelty: penalizes content already present in context

Uses a knapsack-style selector to maximize total utility within a
token budget constraint.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScoredRetrieval:
    """A retrieval result annotated with utility scoring."""
    record: dict[str, Any]
    relevance_score: float
    utility_score: float
    cost: int
    cost_efficiency: float
    factors: dict[str, float] = field(default_factory=dict)
    retrieval_id: str = ""

    def __post_init__(self):
        if not self.retrieval_id:
            self.retrieval_id = f"ret_{int(time.time() * 1000)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "retrieval_id": self.retrieval_id,
            "relevance_score": round(self.relevance_score, 4),
            "utility_score": round(self.utility_score, 4),
            "cost": self.cost,
            "cost_efficiency": round(self.cost_efficiency, 6),
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
        }


@dataclass
class OutcomeRecord:
    """Feedback record for retrieval outcome tracking."""
    retrieval_id: str
    was_useful: bool
    timestamp: float = field(default_factory=time.time)


class RetrievalUtilityScorer:
    """
    Scores retrieval results by multi-dimensional utility and selects
    the highest-value set within a token budget.

    Usage:
        scorer = RetrievalUtilityScorer()
        scored = scorer.score_retrieval(query, results, agent_context)
        selected = scorer.rank_by_utility(scored, budget=5000)
    """

    WEIGHT_RELEVANCE = 0.35
    WEIGHT_RECENCY = 0.20
    WEIGHT_ALIGNMENT = 0.15
    WEIGHT_EFFICIENCY = 0.15
    WEIGHT_NOVELTY = 0.15

    TOKEN_ESTIMATE_RATIO = 0.25  # ~4 chars per token

    def __init__(self):
        self._outcomes: list[OutcomeRecord] = []
        self._max_outcomes = 1000
        self._source_reliability: dict[str, float] = {}

    def score_retrieval(
        self,
        query: str,
        results: list[dict[str, Any]],
        agent_context: dict[str, Any] | None = None,
    ) -> list[ScoredRetrieval]:
        """
        Score each retrieval result's utility across multiple dimensions.

        Args:
            query: the retrieval query string
            results: list of retrieval result dicts, each with at minimum
                     'content', 'score', and optionally 'timestamp', 'tags',
                     'layer', 'source'
            agent_context: optional dict describing the agent's domain and
                           current context keys
        """
        agent_ctx = agent_context or {}
        existing_keys = set(agent_ctx.get("context_keys", []))
        agent_domain = agent_ctx.get("domain", "")

        scored: list[ScoredRetrieval] = []
        for result in results:
            content = str(result.get("content", ""))
            raw_relevance = float(result.get("score", 0.0))
            tokens = self._estimate_tokens(content)

            relevance = min(raw_relevance, 1.0)
            recency = self._score_recency(result.get("timestamp"))
            alignment = self._score_alignment(result, agent_domain)
            efficiency = self._score_efficiency(relevance, tokens)
            novelty = self._score_novelty(content, existing_keys)

            factors = {
                "relevance": relevance,
                "recency": recency,
                "alignment": alignment,
                "efficiency": efficiency,
                "novelty": novelty,
            }

            utility = (
                self.WEIGHT_RELEVANCE * relevance
                + self.WEIGHT_RECENCY * recency
                + self.WEIGHT_ALIGNMENT * alignment
                + self.WEIGHT_EFFICIENCY * efficiency
                + self.WEIGHT_NOVELTY * novelty
            )

            source = result.get("source", "unknown")
            reliability = self._source_reliability.get(source, 0.5)
            utility *= (0.7 + 0.3 * reliability)

            cost_eff = utility / tokens if tokens > 0 else 0.0

            scored.append(ScoredRetrieval(
                record=result,
                relevance_score=relevance,
                utility_score=utility,
                cost=tokens,
                cost_efficiency=cost_eff,
                factors=factors,
            ))

        scored.sort(key=lambda s: s.utility_score, reverse=True)
        return scored

    def rank_by_utility(
        self,
        scored_results: list[ScoredRetrieval],
        budget: int,
    ) -> list[ScoredRetrieval]:
        """
        Knapsack-style selection: maximize total utility within token budget.

        Uses a greedy approach sorted by cost-efficiency (utility/token)
        which approximates the fractional knapsack optimum.
        """
        by_efficiency = sorted(
            scored_results, key=lambda s: s.cost_efficiency, reverse=True,
        )

        selected: list[ScoredRetrieval] = []
        remaining_budget = budget

        for item in by_efficiency:
            if item.cost <= remaining_budget:
                selected.append(item)
                remaining_budget -= item.cost

        selected.sort(key=lambda s: s.utility_score, reverse=True)

        logger.debug(
            "Selected %d/%d results within budget %d (used %d)",
            len(selected), len(scored_results), budget, budget - remaining_budget,
        )
        return selected

    def track_outcome(self, retrieval_id: str, was_useful: bool) -> None:
        """Record feedback on whether a retrieval was actually useful."""
        outcome = OutcomeRecord(retrieval_id=retrieval_id, was_useful=was_useful)
        self._outcomes.append(outcome)
        if len(self._outcomes) > self._max_outcomes:
            self._outcomes = self._outcomes[-self._max_outcomes:]

        self._update_source_reliability()

    def _score_recency(self, timestamp: float | None) -> float:
        """Score recency: recent items score higher, decaying over hours."""
        if timestamp is None:
            return 0.5
        age_hours = (time.time() - timestamp) / 3600.0
        return max(0.0, math.exp(-age_hours / 24.0))

    def _score_alignment(self, result: dict[str, Any], agent_domain: str) -> float:
        """Score how well the result aligns with the agent's domain."""
        if not agent_domain:
            return 0.5

        tags = result.get("tags", [])
        layer = result.get("layer", "")
        content_preview = str(result.get("content", ""))[:200].lower()
        domain_lower = agent_domain.lower()

        score = 0.3
        if domain_lower in content_preview:
            score += 0.3
        if any(domain_lower in str(t).lower() for t in tags):
            score += 0.2
        if layer and domain_lower in layer.lower():
            score += 0.2

        return min(score, 1.0)

    def _score_efficiency(self, relevance: float, tokens: int) -> float:
        """Score cost efficiency: high relevance per token."""
        if tokens <= 0:
            return 0.0
        raw = relevance / (tokens / 100.0)
        return min(raw, 1.0)

    def _score_novelty(self, content: str, existing_keys: set[str]) -> float:
        """Score novelty: penalize content already represented in context."""
        if not existing_keys:
            return 0.8

        content_lower = content.lower()
        overlap_count = sum(1 for k in existing_keys if k.lower() in content_lower)

        if overlap_count == 0:
            return 1.0
        return max(0.1, 1.0 - (overlap_count / max(len(existing_keys), 1)))

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        if not text:
            return 1
        return max(1, int(len(text) * self.TOKEN_ESTIMATE_RATIO))

    def _update_source_reliability(self) -> None:
        """Recompute source reliability scores from outcome history."""
        if len(self._outcomes) < 10:
            return

        source_stats: dict[str, list[bool]] = {}
        for outcome in self._outcomes[-500:]:
            parts = outcome.retrieval_id.split("_")
            source = parts[0] if len(parts) > 1 else "unknown"
            if source not in source_stats:
                source_stats[source] = []
            source_stats[source].append(outcome.was_useful)

        for source, outcomes in source_stats.items():
            if len(outcomes) >= 5:
                self._source_reliability[source] = sum(outcomes) / len(outcomes)
