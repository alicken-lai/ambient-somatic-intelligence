"""
Context Entropy Manager — Information density optimization.

Uses Shannon entropy to quantify information content in context blocks
and detect redundancy across them. This enables:

  - Measuring how much "information" a context block actually carries
  - Detecting cross-block redundancy (duplicate information)
  - Computing optimal compression levels
  - Selecting highest information-density items within budget

Entropy here operates on word-level distributions (not character-level)
to better approximate semantic information content.
"""

from __future__ import annotations

import logging
import math
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EntropyReport:
    """System-wide entropy and redundancy metrics."""
    avg_entropy: float
    min_entropy: float
    max_entropy: float
    redundancy_score: float
    block_count: int
    recommendations: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "avg_entropy": round(self.avg_entropy, 4),
            "min_entropy": round(self.min_entropy, 4),
            "max_entropy": round(self.max_entropy, 4),
            "redundancy_score": round(self.redundancy_score, 4),
            "block_count": self.block_count,
            "recommendations": self.recommendations,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class ContextEntropyManager:
    """
    Measures and optimizes information density in context blocks.

    Usage:
        entropy_mgr = ContextEntropyManager()

        h = entropy_mgr.measure_entropy("The quick brown fox jumps ...")
        redundancy = entropy_mgr.measure_redundancy([block_a, block_b])
        level = entropy_mgr.optimal_compression_level(h, budget=1000)
        selected = entropy_mgr.entropy_weighted_selection(candidates, budget=5000)
    """

    def __init__(self, token_ratio: float = 0.25):
        self._token_ratio = token_ratio
        self._entropy_cache: dict[int, float] = {}
        self._max_cache = 500

    def measure_entropy(self, context_block: str) -> float:
        """
        Compute Shannon entropy of a context block using word-level distribution.

        Returns entropy in bits. Higher entropy = more information density.
        """
        if not context_block or not context_block.strip():
            return 0.0

        cache_key = hash(context_block)
        if cache_key in self._entropy_cache:
            return self._entropy_cache[cache_key]

        words = context_block.lower().split()
        if not words:
            return 0.0

        total = len(words)
        freq = Counter(words)
        entropy = 0.0

        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        self._entropy_cache[cache_key] = entropy
        if len(self._entropy_cache) > self._max_cache:
            oldest_keys = list(self._entropy_cache.keys())[:self._max_cache // 4]
            for k in oldest_keys:
                self._entropy_cache.pop(k, None)

        return entropy

    def measure_redundancy(self, context_blocks: list[str]) -> float:
        """
        Measure cross-block redundancy based on shared vocabulary.

        Returns 0.0 (no redundancy) to 1.0 (fully redundant).
        """
        if len(context_blocks) < 2:
            return 0.0

        word_sets = []
        for block in context_blocks:
            words = set(block.lower().split())
            if words:
                word_sets.append(words)

        if len(word_sets) < 2:
            return 0.0

        total_pairs = 0
        total_overlap = 0.0

        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                intersection = word_sets[i] & word_sets[j]
                union = word_sets[i] | word_sets[j]
                if union:
                    total_overlap += len(intersection) / len(union)
                total_pairs += 1

        return total_overlap / total_pairs if total_pairs > 0 else 0.0

    def optimal_compression_level(self, entropy: float, budget: int) -> float:
        """
        Determine how aggressively to compress based on entropy and budget.

        Returns 0.0 (no compression) to 1.0 (maximum compression).
        Low-entropy content can be compressed more without losing information.
        """
        if budget <= 0:
            return 1.0
        if entropy <= 0:
            return 0.9

        max_entropy = 12.0
        normalized_entropy = min(entropy / max_entropy, 1.0)

        budget_pressure = max(0.0, 1.0 - (budget / 10000.0))

        compression = budget_pressure * (1.0 - normalized_entropy * 0.6)

        return max(0.0, min(1.0, compression))

    def entropy_weighted_selection(
        self,
        candidates: list[dict[str, Any]],
        budget: int,
    ) -> list[dict[str, Any]]:
        """
        Select highest information-density items within token budget.

        Each candidate must have a 'content' key. Returns selected items
        sorted by information density (entropy per token).
        """
        scored: list[tuple[dict[str, Any], float, int]] = []

        for candidate in candidates:
            content = str(candidate.get("content", ""))
            tokens = self._estimate_tokens(content)
            entropy = self.measure_entropy(content)
            density = entropy / max(tokens, 1)
            scored.append((candidate, density, tokens))

        scored.sort(key=lambda x: x[1], reverse=True)

        selected: list[dict[str, Any]] = []
        remaining = budget

        for candidate, density, tokens in scored:
            if tokens <= remaining:
                selected.append(candidate)
                remaining -= tokens

        logger.debug(
            "Entropy selection: %d/%d candidates, %d/%d tokens used",
            len(selected), len(candidates), budget - remaining, budget,
        )
        return selected

    def get_entropy_report(self, context_blocks: list[str] | None = None) -> EntropyReport:
        """Generate a system-wide entropy report."""
        blocks = context_blocks or []

        if not blocks:
            return EntropyReport(
                avg_entropy=0.0,
                min_entropy=0.0,
                max_entropy=0.0,
                redundancy_score=0.0,
                block_count=0,
                recommendations=["No context blocks provided for analysis"],
            )

        entropies = [self.measure_entropy(b) for b in blocks]
        redundancy = self.measure_redundancy(blocks)

        avg_e = sum(entropies) / len(entropies)
        min_e = min(entropies)
        max_e = max(entropies)

        recommendations = self._generate_recommendations(
            avg_e, min_e, max_e, redundancy, len(blocks),
        )

        return EntropyReport(
            avg_entropy=avg_e,
            min_entropy=min_e,
            max_entropy=max_e,
            redundancy_score=redundancy,
            block_count=len(blocks),
            recommendations=recommendations,
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        if not text:
            return 1
        return max(1, int(len(text) * self._token_ratio))

    @staticmethod
    def _generate_recommendations(
        avg_entropy: float,
        min_entropy: float,
        max_entropy: float,
        redundancy: float,
        block_count: int,
    ) -> list[str]:
        """Generate actionable recommendations based on entropy metrics."""
        recs: list[str] = []

        if redundancy > 0.5:
            recs.append(
                f"High redundancy ({redundancy:.0%}) — deduplicate or merge "
                f"overlapping context blocks"
            )
        elif redundancy > 0.3:
            recs.append(
                f"Moderate redundancy ({redundancy:.0%}) — consider consolidating "
                f"similar blocks"
            )

        if min_entropy < 1.0 and block_count > 1:
            recs.append(
                f"Low-entropy block detected (min={min_entropy:.2f} bits) — "
                f"candidate for aggressive compression"
            )

        if max_entropy - min_entropy > 4.0:
            recs.append(
                f"Wide entropy variance ({min_entropy:.1f}–{max_entropy:.1f} bits) — "
                f"normalize information density across blocks"
            )

        if avg_entropy > 8.0:
            recs.append(
                "High average entropy — context is information-dense, "
                "avoid lossy compression"
            )

        if not recs:
            recs.append("Context entropy is within optimal range")

        return recs
