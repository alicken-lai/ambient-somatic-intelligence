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
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Phase A (observe-only): wire the existing memory ontology in for read-only
# decay projections and integrity observability. Guarded import so AgentMemory
# keeps working even if the ontology package is unavailable.
try:
    from memory.ontology.layer_definition import MemoryLayer
    from memory.ontology.decay_rules import DECAY_RULE_REGISTRY, compute_decay
    from memory.ontology.promotion_rules import (
        PROMOTION_RULES,
        check_promotion_eligibility,
    )
    _ONTOLOGY_AVAILABLE = True
except Exception:  # pragma: no cover - defensive fallback
    MemoryLayer = None  # type: ignore[assignment]
    DECAY_RULE_REGISTRY = {}  # type: ignore[assignment]
    compute_decay = None  # type: ignore[assignment]
    PROMOTION_RULES = []  # type: ignore[assignment]
    check_promotion_eligibility = None  # type: ignore[assignment]
    _ONTOLOGY_AVAILABLE = False


AGENTS_MEMORY_DIR = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os")) / "state" / "agents"

# Category -> ontology layer (int value matching MemoryLayer). Used in Phase A
# only to LABEL entries for observability; gating/confidence stay unchanged
# until Phase B promotes this into an enforced rule.
_CATEGORY_TO_LAYER: dict[str, int] = {
    "knowledge": 1,
    "pattern": 1,
    "preference": 1,
    "failure": 2,
    "instinct": 2,
    "skill": 3,
    "strategy": 4,
}


def category_to_layer(category: str) -> int:
    """Map a free-form memory category to its ontology layer value (default L1)."""
    return _CATEGORY_TO_LAYER.get(category, 1)


# Phase B (enforce-by-default): new entries enter at L1 with a capped initial
# confidence; higher layers must be earned through promote(). This is a DEFAULT
# behavior change, not an opt-in flag.
INITIAL_CONFIDENCE_CAP: float = 0.5


def _enforcement_enabled() -> bool:
    """Phase B enforcement is ON by default.

    Emergency rollback only: set AMBIENT_OS_MEMORY_ENFORCE=0 to fall back to the
    Phase A observe-only semantics. Read at call time so it is test-friendly.
    """
    return os.environ.get("AMBIENT_OS_MEMORY_ENFORCE", "1") != "0"


def _is_allow(token: Any) -> bool:
    """Interpret a governance token as a Guardian ALLOW decision."""
    if token is None:
        return False
    if isinstance(token, str):
        return token.upper() == "ALLOW"
    if isinstance(token, dict):
        return str(token.get("risk", "")).upper() == "ALLOW"
    return str(getattr(token, "risk", "")).upper() == "ALLOW"


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
    # Phase A additions (ontology alignment). Default L1 keeps legacy entries safe.
    layer: int = 1
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    # Phase B additions: outcome counters + cross-context validation, so the
    # ontology promotion gate can consume agent memory directly.
    success_count: int = 0
    failure_count: int = 0
    contexts_validated: list[str] = field(default_factory=list)

    @property
    def timestamp(self) -> datetime:
        """Creation time as aware datetime (ontology DecayEngine compatibility)."""
        return datetime.fromtimestamp(self.created, tz=timezone.utc)

    @property
    def last_accessed(self) -> datetime:
        """Last-use time as aware datetime (falls back to creation time)."""
        ref = self.last_used or self.created
        return datetime.fromtimestamp(ref, tz=timezone.utc)

    @property
    def access_count(self) -> int:
        """Adapter: promotion gate reads occurrences from access_count."""
        return self.uses

    def success_rate(self) -> float:
        """Adapter: promotion gate reads success rate from this callable."""
        total = self.success_count + self.failure_count
        return (self.success_count / total) if total else 0.0

    def layer_enum(self) -> "MemoryLayer":
        """Return the ontology MemoryLayer for this entry's int layer."""
        return MemoryLayer(self.layer)

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
            "layer": self.layer,
            "entry_id": self.entry_id,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "contexts_validated": self.contexts_validated,
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
            layer=data.get("layer", category_to_layer(data.get("category", "knowledge"))),
            entry_id=data.get("entry_id") or uuid.uuid4().hex[:12],
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            contexts_validated=data.get("contexts_validated", []),
        )


@dataclass
class PromotionResult:
    """Outcome of an attempted single-step layer promotion."""
    ok: bool
    entry_id: str
    from_layer: int
    to_layer: int | None
    blocking_reasons: list[str]


class _EligibilityView:
    """Adapter exposing a MemoryEntry to the ontology promotion gate.

    check_promotion_eligibility expects entry.layer to be a MemoryLayer (it
    reads .name) and pulls stats via access_count / success_rate() /
    contexts_validated. This view bridges the int-backed MemoryEntry without
    mutating it.
    """

    def __init__(self, entry: "MemoryEntry") -> None:
        self._entry = entry
        self.layer = MemoryLayer(entry.layer)
        self.confidence = entry.confidence
        self.access_count = entry.access_count
        self.contexts_validated = entry.contexts_validated

    def success_rate(self) -> float:
        return self._entry.success_rate()


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
        """Store a new memory entry.

        Phase B default behavior (enforce-by-default): every new entry enters at
        L1 with a capped initial confidence, regardless of category. The
        requested high layer is recorded only as a candidate target in
        metadata['target_layer']; it can only be granted later via promote().
        Set AMBIENT_OS_MEMORY_ENFORCE=0 to fall back to Phase A semantics.
        """
        md = dict(metadata or {})
        md.setdefault("author", self.agent_id)

        if _enforcement_enabled():
            requested_layer = category_to_layer(category)
            if requested_layer > 1:
                md.setdefault("target_layer", requested_layer)
            layer = 1
            confidence = min(confidence, INITIAL_CONFIDENCE_CAP)
        else:
            layer = category_to_layer(category)

        entry = MemoryEntry(
            content=content,
            category=category,
            tags=tags or [],
            confidence=confidence,
            metadata=md,
            layer=layer,
        )
        self._entries.append(entry)

        if len(self._entries) > self.max_entries:
            self._evict()

        self._save()
        return entry

    def seed_knowledge(
        self,
        content: str,
        *,
        tags: list[str] | None = None,
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Preload knowledge safely (for bootstrap/seed data).

        Always lands at L1 with confidence <= INITIAL_CONFIDENCE_CAP and is
        tagged metadata['origin']='preloaded' so it can never masquerade as an
        earned high-layer strategy.
        """
        md = dict(metadata or {})
        md["origin"] = "preloaded"
        md.setdefault("author", self.agent_id)

        entry = MemoryEntry(
            content=content,
            category="knowledge",
            tags=tags or [],
            confidence=min(confidence, INITIAL_CONFIDENCE_CAP),
            metadata=md,
            layer=1,
        )
        self._entries.append(entry)

        if len(self._entries) > self.max_entries:
            self._evict()

        self._save()
        return entry

    def promote(
        self,
        entry: MemoryEntry,
        target_layer: "MemoryLayer | int",
        *,
        governance_token: Any = None,
        verifier: Any = None,
    ) -> PromotionResult:
        """Attempt a single-step promotion of an entry to a higher layer.

        Enforces the ontology promotion rules plus governance/verifier gates:
          - requires_governance: governance_token must be a Guardian ALLOW;
          - requires_verifier: verifier.identity must differ from the entry
            author (no self-verification, per freeze doctrine).
        On failure, returns ok=False with blocking_reasons and leaves the entry
        untouched.
        """
        from_layer = int(entry.layer)
        if not _ONTOLOGY_AVAILABLE:
            return PromotionResult(False, entry.entry_id, from_layer, None,
                                   ["ontology unavailable"])

        target_val = int(target_layer)
        rule = next(
            (r for r in PROMOTION_RULES
             if int(r.source_layer) == from_layer and int(r.target_layer) == target_val),
            None,
        )
        if rule is None:
            return PromotionResult(
                False, entry.entry_id, from_layer, None,
                [f"no single-step promotion rule for {from_layer}->{target_val}"],
            )

        eligible, reasons = check_promotion_eligibility(_EligibilityView(entry), rule)
        reasons = list(reasons)

        if rule.requires_governance and not _is_allow(governance_token):
            reasons.append("governance approval required (token != ALLOW)")

        if rule.requires_verifier:
            verifier_id = getattr(verifier, "identity", None)
            author = entry.metadata.get("author")
            if verifier_id is None:
                reasons.append("independent verifier required")
            elif author is not None and verifier_id == author:
                reasons.append("verifier must differ from author (no self-verification)")

        if reasons:
            return PromotionResult(False, entry.entry_id, from_layer, None, reasons)

        entry.layer = target_val
        entry.metadata["promoted_from"] = from_layer
        self._save()
        return PromotionResult(True, entry.entry_id, from_layer, target_val, [])

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

    def decay_report(self, now: datetime | None = None) -> list[dict[str, Any]]:
        """Observe-only confidence decay projection (Phase A: recommendations only).

        Computes each entry's projected confidence under the ontology decay rules
        WITHOUT mutating, deleting, or saving anything. Returns a list of
        recommendations (retain/archive/remove) for downstream observability.
        Enforcement is deferred to a later, governed phase.
        """
        if not _ONTOLOGY_AVAILABLE:
            return []
        now = now or datetime.now(tz=timezone.utc)
        reports: list[dict[str, Any]] = []
        for entry in self._entries:
            rule = DECAY_RULE_REGISTRY.get(MemoryLayer(entry.layer))
            if rule is None:
                continue
            projected = compute_decay(entry, rule, now)
            margin = projected - rule.min_confidence
            if projected <= rule.min_confidence:
                action = "remove"
            elif margin < 0.1:
                action = "archive"
            else:
                action = "retain"
            reports.append({
                "entry_id": entry.entry_id,
                "layer": int(entry.layer),
                "category": entry.category,
                "current_confidence": round(entry.confidence, 4),
                "projected_confidence": round(projected, 4),
                "recommended_action": action,
                "content_preview": entry.content[:60],
            })
        return reports

    def integrity_warnings(self) -> list[dict[str, Any]]:
        """Observe-only detector for the init back door (Phase A).

        Flags high-layer entries (skill/strategic) that carry near-maximum
        confidence yet have never been used. These are the hallmark of
        pre-loaded memories that bypassed the promotion chain. Read-only.
        """
        warnings: list[dict[str, Any]] = []
        for entry in self._entries:
            if entry.layer >= 3 and entry.uses == 0 and entry.confidence >= 0.9:
                warnings.append({
                    "entry_id": entry.entry_id,
                    "category": entry.category,
                    "layer": int(entry.layer),
                    "confidence": entry.confidence,
                    "reason": "high-layer entry with zero uses and >=0.9 confidence (possible init-bypass)",
                    "content_preview": entry.content[:60],
                })
        return warnings

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
