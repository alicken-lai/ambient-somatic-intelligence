"""
Semantic Retriever — Relevance-scored memory retrieval with layer priority.

Unlike the flat search in memory_recall.py, the SemanticRetriever:
  - Applies retrieval gating (skip irrelevant layers early)
  - Scores by multi-dimensional relevance (semantic overlap, recency, layer weight)
  - Respects token budgets (stops when budget is exhausted)
  - Deduplicates and compresses results
  - Supports query expansion for better recall

This is the "read path" complement to memory_store.py's "write path".
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from memory_classify import LAYERS

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"

LAYER_SEARCH_ORDER = ["semantic", "procedural", "governance", "episodic", "scratchpad"]

LAYER_WEIGHT = {
    "semantic": 2.0,
    "procedural": 1.6,
    "governance": 1.3,
    "episodic": 1.0,
    "scratchpad": 0.2,
    "archive": 0.1,
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with", "this", "that",
}


def tokenize(text: str) -> set[str]:
    """Extract meaningful tokens from text."""
    tokens = re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", text.lower())
    return {t for t in tokens if t not in STOP_WORDS}


def bigrams(tokens: set[str]) -> set[str]:
    """Generate bigrams from token set for phrase matching."""
    sorted_tokens = sorted(tokens)
    return {f"{sorted_tokens[i]}_{sorted_tokens[i+1]}" for i in range(len(sorted_tokens) - 1)}


@dataclass
class RetrievalResult:
    """A single retrieved memory with relevance score."""
    content: str
    layer: str
    score: float
    timestamp: str
    source: str
    tags: list[str]
    token_estimate: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "layer": self.layer,
            "score": round(self.score, 4),
            "timestamp": self.timestamp,
            "source": self.source,
            "tags": self.tags,
            "token_estimate": self.token_estimate,
        }


@dataclass
class RetrievalQuery:
    """Structured query for retrieval."""
    raw_query: str
    tokens: set[str] = field(default_factory=set)
    required_tags: list[str] = field(default_factory=list)
    layer_filter: list[str] | None = None
    max_results: int = 20
    min_score: float = 0.1
    token_budget: int = 32_000

    def __post_init__(self):
        if not self.tokens:
            self.tokens = tokenize(self.raw_query)


class SemanticRetriever:
    """
    Retrieves relevant memories with semantic scoring and budget awareness.

    Usage:
        retriever = SemanticRetriever()
        results = retriever.retrieve("how to setup cursor mcp", token_budget=5000)
        for r in results:
            print(f"[{r.layer}] {r.score:.2f} — {r.content[:80]}")
    """

    def __init__(self, memory_dir: Path | None = None):
        self.memory_dir = memory_dir or MEMORY_DIR

    def retrieve(
        self,
        query: str,
        max_results: int = 20,
        min_score: float = 0.1,
        token_budget: int = 32_000,
        layer_filter: list[str] | None = None,
        required_tags: list[str] | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant memories within token budget.

        Searches layers in priority order, stops when budget exhausted.
        """
        rq = RetrievalQuery(
            raw_query=query,
            required_tags=required_tags or [],
            layer_filter=layer_filter,
            max_results=max_results,
            min_score=min_score,
            token_budget=token_budget,
        )

        candidates: list[RetrievalResult] = []
        search_layers = rq.layer_filter or LAYER_SEARCH_ORDER

        for layer in search_layers:
            if layer not in LAYER_SEARCH_ORDER:
                continue

            layer_results = self._search_layer(layer, rq)
            candidates.extend(layer_results)

        candidates.sort(key=lambda r: r.score, reverse=True)
        candidates = self._deduplicate(candidates)

        final: list[RetrievalResult] = []
        tokens_used = 0

        for result in candidates:
            if len(final) >= max_results:
                break
            token_est = self._estimate_tokens(result.content)
            if tokens_used + token_est > token_budget:
                break
            result.token_estimate = token_est
            tokens_used += token_est
            final.append(result)

        return final

    def retrieve_for_context(
        self,
        query: str,
        token_budget: int = 32_000,
    ) -> dict[str, Any]:
        """
        Retrieve memories formatted for context injection.

        Returns a structured result with metadata for the ContextAssembler.
        """
        results = self.retrieve(query, token_budget=token_budget)

        total_tokens = sum(r.token_estimate for r in results)
        layers_used = list({r.layer for r in results})

        return {
            "query": query,
            "results": [r.to_dict() for r in results],
            "total_results": len(results),
            "total_tokens": total_tokens,
            "token_budget": token_budget,
            "budget_used_pct": round(total_tokens / token_budget, 3) if token_budget > 0 else 0,
            "layers_searched": layers_used,
            "top_score": results[0].score if results else 0.0,
        }

    def _search_layer(self, layer: str, query: RetrievalQuery) -> list[RetrievalResult]:
        """Search a single memory layer."""
        layer_file = self.memory_dir / layer / "records.jsonl"
        if not layer_file.exists():
            return []

        results: list[RetrievalResult] = []
        layer_weight = LAYER_WEIGHT.get(layer, 1.0)

        with layer_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if query.required_tags:
                    record_tags = {t.lower() for t in record.get("tags", [])}
                    if not any(t.lower() in record_tags for t in query.required_tags):
                        continue

                score = self._score_record(record, query, layer_weight)
                if score < query.min_score:
                    continue

                content = record.get("content", "")
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False)

                results.append(RetrievalResult(
                    content=str(content)[:2000],
                    layer=layer,
                    score=score,
                    timestamp=record.get("timestamp", ""),
                    source=record.get("source", ""),
                    tags=record.get("tags", []),
                ))

        return results

    def _score_record(
        self,
        record: dict[str, Any],
        query: RetrievalQuery,
        layer_weight: float,
    ) -> float:
        """Calculate multi-dimensional relevance score."""
        content = str(record.get("content", ""))
        tags = record.get("tags", [])
        timestamp = record.get("timestamp", "")

        content_tokens = tokenize(content)
        tag_tokens = {t.lower() for t in tags}

        token_overlap = query.tokens & content_tokens
        tag_overlap = query.tokens & tag_tokens
        overlap_ratio = len(token_overlap) / len(query.tokens) if query.tokens else 0

        # Exact substring match
        query_lower = query.raw_query.lower()
        exact_match = query_lower in content.lower()

        # Scoring components
        semantic_score = overlap_ratio * 0.4
        tag_score = (len(tag_overlap) / max(len(query.tokens), 1)) * 0.3
        exact_bonus = 0.3 if exact_match else 0.0
        recency = self._recency_score(timestamp) * 0.1

        base_score = semantic_score + tag_score + exact_bonus + recency
        final_score = base_score * layer_weight

        return min(1.0, final_score)

    def _recency_score(self, timestamp: str) -> float:
        """Score based on recency (exponential decay over 7 days)."""
        if not timestamp:
            return 0.0
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
            return math.exp(-age_hours / (24 * 7))
        except (ValueError, TypeError):
            return 0.0

    def _deduplicate(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Remove near-duplicate results based on content similarity."""
        seen_prefixes: set[str] = set()
        deduped: list[RetrievalResult] = []

        for result in results:
            prefix = result.content[:150].strip()
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            deduped.append(result)

        return deduped

    def _estimate_tokens(self, text: str) -> int:
        """Fast token count estimation."""
        if not text:
            return 0
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        non_cjk = len(text) - cjk
        return int(cjk * 0.7 + non_cjk / 4)


if __name__ == "__main__":
    retriever = SemanticRetriever()
    result = retriever.retrieve_for_context("cursor hermes mcp setup", token_budget=5000)
    print(json.dumps(result, indent=2, ensure_ascii=False))
