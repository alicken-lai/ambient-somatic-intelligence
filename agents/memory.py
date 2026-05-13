"""
Agent Memory — Per-agent local knowledge store.

Each agent maintains its own memory with:
  - Domain knowledge (facts, patterns specific to its specialty)
  - Execution history (what worked, what failed, in what context)
  - Learned strategies (reusable approaches to common tasks)
  - Preferences (tools, patterns, anti-patterns)

This is separate from the global memory system — it's the agent's
personal experience that shapes future behavior.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


AGENTS_MEMORY_DIR = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os")) / "state" / "agents"


@dataclass
class MemoryEntry:
    """A single entry in an agent's local memory."""
    content: str
    category: str  # knowledge, strategy, failure, preference, pattern
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0
    uses: int = 0
    last_used: float = 0
    created: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "confidence": self.confidence,
            "uses": self.uses,
            "last_used": self.last_used,
            "created": self.created,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MemoryEntry":
        return MemoryEntry(
            content=data["content"],
            category=data["category"],
            tags=data.get("tags", []),
            confidence=data.get("confidence", 1.0),
            uses=data.get("uses", 0),
            last_used=data.get("last_used", 0),
            created=data.get("created", time.time()),
            metadata=data.get("metadata", {}),
        )


class AgentMemory:
    """
    Per-agent local knowledge store.

    Usage:
        mem = AgentMemory("frontend-agent")

        # Store knowledge
        mem.remember("React useCallback prevents unnecessary re-renders",
                     category="knowledge", tags=["react", "performance"])

        mem.remember("Use Tailwind @apply for repeated patterns",
                     category="strategy", tags=["css", "tailwind"])

        # Recall
        results = mem.recall("react performance", limit=5)

        # Learn from failure
        mem.remember("Don't use useMemo for simple calculations — overhead > benefit",
                     category="failure", tags=["react", "anti-pattern"])
    """

    def __init__(self, agent_id: str, max_entries: int = 500):
        self.agent_id = agent_id
        self.max_entries = max_entries
        self._entries: list[MemoryEntry] = []
        self._memory_dir = AGENTS_MEMORY_DIR / agent_id / "memory"
        self._load()

    def remember(
        self,
        content: str,
        category: str = "knowledge",
        tags: list[str] | None = None,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Store a new memory entry."""
        entry = MemoryEntry(
            content=content,
            category=category,
            tags=tags or [],
            confidence=confidence,
            metadata=metadata or {},
        )
        self._entries.append(entry)

        if len(self._entries) > self.max_entries:
            self._evict()

        self._save()
        return entry

    def recall(
        self,
        query: str,
        category: str | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Recall memories by relevance to query."""
        candidates = self._entries

        if category:
            candidates = [e for e in candidates if e.category == category]

        if tags:
            tag_set = set(tags)
            candidates = [e for e in candidates if tag_set & set(e.tags)]

        scored = []
        query_tokens = set(query.lower().split())
        for entry in candidates:
            score = self._score_entry(entry, query_tokens)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [entry for _, entry in scored[:limit]]

        for entry in results:
            entry.uses += 1
            entry.last_used = time.time()

        return results

    def recall_strategies(self, task_type: str) -> list[MemoryEntry]:
        """Recall strategies relevant to a task type."""
        return self.recall(task_type, category="strategy", limit=5)

    def recall_failures(self, context: str) -> list[MemoryEntry]:
        """Recall past failures to avoid repeating mistakes."""
        return self.recall(context, category="failure", limit=5)

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        categories: dict[str, int] = {}
        for e in self._entries:
            categories[e.category] = categories.get(e.category, 0) + 1

        return {
            "agent_id": self.agent_id,
            "total_entries": len(self._entries),
            "by_category": categories,
            "most_used": self._most_used(5),
            "capacity_used": f"{len(self._entries)}/{self.max_entries}",
        }

    def _score_entry(self, entry: MemoryEntry, query_tokens: set[str]) -> float:
        """Score an entry's relevance to a query."""
        content_tokens = set(entry.content.lower().split())
        tag_tokens = set(t.lower() for t in entry.tags)
        all_tokens = content_tokens | tag_tokens

        overlap = query_tokens & all_tokens
        if not overlap:
            return 0.0

        base_score = len(overlap) / max(len(query_tokens), 1)
        confidence_boost = entry.confidence * 0.3
        use_boost = min(entry.uses * 0.05, 0.3)
        recency = min((time.time() - entry.created) / 86400, 30) / 30
        recency_boost = (1 - recency) * 0.2

        return base_score + confidence_boost + use_boost + recency_boost

    def _most_used(self, limit: int) -> list[dict[str, Any]]:
        """Get most frequently used entries."""
        sorted_entries = sorted(self._entries, key=lambda e: e.uses, reverse=True)
        return [{"content": e.content[:80], "uses": e.uses, "category": e.category}
                for e in sorted_entries[:limit]]

    def _evict(self) -> None:
        """Evict lowest-value entries when at capacity."""
        now = time.time()
        for entry in self._entries:
            age_days = (now - entry.created) / 86400
            entry.metadata["_eviction_score"] = (
                entry.confidence * 0.4
                + min(entry.uses * 0.1, 0.3)
                + (1 - min(age_days / 60, 1)) * 0.3
            )
        self._entries.sort(key=lambda e: e.metadata.get("_eviction_score", 0), reverse=True)
        self._entries = self._entries[: self.max_entries]

    def _save(self) -> None:
        """Persist memory to disk."""
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._memory_dir / "entries.jsonl"
        try:
            with open(filepath, "w") as f:
                for entry in self._entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")
        except OSError:
            pass

    def _load(self) -> None:
        """Load memory from disk."""
        filepath = self._memory_dir / "entries.jsonl"
        if not filepath.exists():
            return
        try:
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        self._entries.append(MemoryEntry.from_dict(data))
        except (json.JSONDecodeError, OSError):
            pass
