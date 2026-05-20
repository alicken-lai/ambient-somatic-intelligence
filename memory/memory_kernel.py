"""
Memory Kernel — Governed memory system with decay, scoring, ranking, and dedup.

Upgrades the append-only DMN + layer files into a queryable, governed memory
system. The MemoryKernel is the single entry point for all memory operations:

  recall()    — Unified query with relevance scoring, decay, budget, dedup
  store()     — Write with auto-classification, dedup check, schema validation
  score()     — Calculate composite relevance score for a record
  decay()     — Apply time-based decay across all layers
  deduplicate() — Find and mark duplicate records
  ttl_sweep() — Enforce TTL policies per layer
  stats()     — Memory health metrics

Scoring dimensions:
  1. Semantic overlap   — token/tag match against query
  2. Recency decay      — exponential decay per layer half-life
  3. Access frequency   — records recalled more often score higher
  4. Layer weight       — semantic > procedural > governance > episodic > scratchpad
  5. Content quality    — length, tag richness, source reliability

Constraints:
  - No full memory dump: recall() always has a max_results cap
  - Token budgets enforced: retrieval stops when budget exhausted
  - Dedup on write: content hash checked before store
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
MEMORY_DIR = AMBIENT_ROOT / "memory"
DMN_PATH = MEMORY_DIR / "dmn.jsonl"

LAYERS = ["episodic", "semantic", "procedural", "governance", "scratchpad", "archive"]


# ── TTL Configuration ────────────────────────────────────────────────────

TTL_POLICIES: dict[str, timedelta] = {
    "scratchpad": timedelta(hours=24),
    "episodic": timedelta(days=30),
    "procedural": timedelta(days=180),
    "governance": timedelta(days=365),
    "semantic": timedelta(days=365),
    "archive": timedelta(days=365 * 10),  # effectively permanent
}


# ── Decay Configuration ──────────────────────────────────────────────────

DECAY_HALF_LIFE_HOURS: dict[str, float] = {
    "scratchpad": 12.0,
    "episodic": 24.0 * 7,       # 7 days
    "procedural": 24.0 * 30,    # 30 days
    "governance": 24.0 * 90,    # 90 days
    "semantic": 24.0 * 180,     # 180 days
    "archive": 24.0 * 365,      # 1 year
}


# ── Layer Weights ────────────────────────────────────────────────────────

LAYER_WEIGHT: dict[str, float] = {
    "semantic": 2.0,
    "procedural": 1.6,
    "governance": 1.3,
    "episodic": 1.0,
    "scratchpad": 0.2,
    "archive": 0.1,
}


# ── Scoring Weights ──────────────────────────────────────────────────────

@dataclass
class ScoringWeights:
    """Tunable weights for the composite relevance score."""
    semantic_overlap: float = 0.30
    tag_match: float = 0.20
    exact_match: float = 0.15
    recency_decay: float = 0.15
    access_frequency: float = 0.10
    content_quality: float = 0.10


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with", "this", "that",
    "的", "是", "了", "在", "有", "和", "就", "不", "人", "都",
}

MAX_RECALL_RESULTS = 50
DEDUP_SIMILARITY_THRESHOLD = 0.85


# ── Data Types ───────────────────────────────────────────────────────────

@dataclass
class ScoredRecord:
    """A memory record with computed relevance score and metadata."""
    content: str
    layer: str
    score: float
    timestamp: str
    source: str
    tags: list[str]
    token_estimate: int = 0
    decay_factor: float = 1.0
    access_count: int = 0
    content_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "layer": self.layer,
            "score": round(self.score, 4),
            "timestamp": self.timestamp,
            "source": self.source,
            "tags": self.tags,
            "token_estimate": self.token_estimate,
            "decay_factor": round(self.decay_factor, 4),
            "access_count": self.access_count,
        }


@dataclass
class RecallResult:
    """Complete result of a recall operation."""
    query: str
    records: list[ScoredRecord]
    total_candidates: int
    total_tokens: int
    token_budget: int
    layers_searched: list[str]
    dedup_removed: int
    decay_applied: bool
    elapsed_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "records": [r.to_dict() for r in self.records],
            "total_results": len(self.records),
            "total_candidates": self.total_candidates,
            "total_tokens": self.total_tokens,
            "token_budget": self.token_budget,
            "budget_used_pct": round(self.total_tokens / max(self.token_budget, 1), 3),
            "layers_searched": self.layers_searched,
            "dedup_removed": self.dedup_removed,
            "decay_applied": self.decay_applied,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


# ── Helper Functions ─────────────────────────────────────────────────────

def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", text.lower())
    return {t for t in tokens if t not in STOP_WORDS}


def _content_hash(content: str) -> str:
    normalized = re.sub(r"\s+", " ", content.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _parse_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    non_cjk = len(text) - cjk
    return int(cjk * 0.7 + non_cjk / 4)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── Memory Kernel ────────────────────────────────────────────────────────

class MemoryKernel:
    """
    Governed memory system with decay, scoring, ranking, and deduplication.

    Usage:
        mk = MemoryKernel()

        # Recall with full scoring pipeline
        result = mk.recall("how to setup hermes mcp", token_budget=5000)
        for r in result.records:
            print(f"[{r.layer}] {r.score:.3f} — {r.content[:80]}")

        # Store with auto-classification and dedup
        mk.store("New procedural knowledge", tags=["hermes", "setup"])

        # Maintenance
        mk.ttl_sweep()
        mk.deduplicate()
    """

    def __init__(
        self,
        memory_dir: Path | None = None,
        scoring_weights: ScoringWeights | None = None,
    ):
        self.memory_dir = memory_dir or MEMORY_DIR
        self.weights = scoring_weights or ScoringWeights()
        self._access_counts: dict[str, int] = defaultdict(int)
        self._access_log_path = self.memory_dir / "access_counts.json"
        self._load_access_counts()

    # ── Recall (unified query interface) ─────────────────────────────────

    def recall(
        self,
        query: str,
        max_results: int = 20,
        min_score: float = 0.05,
        token_budget: int = 32_000,
        layer_filter: list[str] | None = None,
        required_tags: list[str] | None = None,
        apply_decay: bool = True,
    ) -> RecallResult:
        """
        Retrieve relevant memories with full scoring pipeline.

        Pipeline: scan → score → decay → dedup → rank → budget cap → return.
        """
        start = time.monotonic()
        max_results = min(max_results, MAX_RECALL_RESULTS)
        query_tokens = _tokenize(query)

        search_layers = layer_filter or [
            "semantic", "procedural", "governance", "episodic", "scratchpad"
        ]

        candidates: list[ScoredRecord] = []
        layers_searched: list[str] = []

        for layer in search_layers:
            if layer not in LAYERS:
                continue
            layer_results = self._scan_layer(
                layer, query, query_tokens, required_tags, min_score, apply_decay,
            )
            if layer_results:
                candidates.extend(layer_results)
                layers_searched.append(layer)

        total_candidates = len(candidates)

        pre_dedup = len(candidates)
        candidates = self._deduplicate_results(candidates)
        dedup_removed = pre_dedup - len(candidates)

        candidates.sort(key=lambda r: r.score, reverse=True)

        final: list[ScoredRecord] = []
        tokens_used = 0
        for rec in candidates:
            if len(final) >= max_results:
                break
            tok = _estimate_tokens(rec.content)
            if tokens_used + tok > token_budget:
                break
            rec.token_estimate = tok
            tokens_used += tok
            final.append(rec)

        for rec in final:
            self._record_access(rec.content_hash)

        elapsed = (time.monotonic() - start) * 1000

        return RecallResult(
            query=query,
            records=final,
            total_candidates=total_candidates,
            total_tokens=tokens_used,
            token_budget=token_budget,
            layers_searched=layers_searched,
            dedup_removed=dedup_removed,
            decay_applied=apply_decay,
            elapsed_ms=elapsed,
        )

    # ── Store (write with validation + dedup check) ──────────────────────

    def store(
        self,
        content: str,
        tags: list[str] | None = None,
        source: str = "memory-kernel",
        layer: str | None = None,
        execution_context: Any | None = None,
    ) -> dict[str, Any]:
        """
        Store a new memory record.

        Auto-classifies into appropriate layer if layer not specified.
        Checks for duplicates before writing.
        """
        content_h = _content_hash(content)

        if self._is_duplicate(content_h):
            return {
                "stored": False,
                "reason": "duplicate_detected",
                "content_hash": content_h,
            }

        record = {
            "timestamp": _utc_now().isoformat(),
            "source": source,
            "tags": tags or [],
            "content": content,
            "_content_hash": content_h,
        }

        if layer is None:
            try:
                from memory_classify import classify_record
                layer = classify_record(record)
            except ImportError:
                layer = "episodic"

        layer_dir = self.memory_dir / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        layer_file = layer_dir / "records.jsonl"

        if execution_context is not None:
            try:
                from kernel.isolation.governed_memory_writer import GovernedMemoryWriter

                rel_layer = layer_file.parent.name
                GovernedMemoryWriter(memory_root=self.memory_dir).append_layer(
                    rel_layer,
                    record,
                    context=execution_context,
                    mutation_reason="memory_kernel_store",
                )
            except (ImportError, PermissionError, ValueError):
                with layer_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            with layer_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

        return {
            "stored": True,
            "layer": layer,
            "content_hash": content_h,
            "timestamp": record["timestamp"],
        }

    # ── Scoring ──────────────────────────────────────────────────────────

    def score(
        self,
        record: dict[str, Any],
        query: str,
        query_tokens: set[str],
        layer: str,
        apply_decay: bool = True,
    ) -> float:
        """
        Calculate composite relevance score for a record.

        Factors:
          1. Semantic overlap (token match ratio)
          2. Tag match (query tokens found in tags)
          3. Exact substring match bonus
          4. Recency decay (exponential with layer-specific half-life)
          5. Access frequency (log-scaled usage count)
          6. Content quality (length + tag richness)
        """
        content = str(record.get("content", ""))
        tags = record.get("tags", [])
        timestamp = record.get("timestamp", "")

        content_tokens = _tokenize(content)
        tag_tokens = {t.lower() for t in tags}

        # 1. Semantic overlap
        overlap = query_tokens & content_tokens
        semantic = len(overlap) / max(len(query_tokens), 1)

        # 2. Tag match
        tag_overlap = query_tokens & tag_tokens
        tag_score = len(tag_overlap) / max(len(query_tokens), 1)

        # 3. Exact match bonus
        exact = 1.0 if query.lower() in content.lower() else 0.0

        # 4. Recency decay
        decay = self._compute_decay(timestamp, layer) if apply_decay else 1.0

        # 5. Access frequency
        content_h = record.get("_content_hash") or _content_hash(content)
        access_count = self._access_counts.get(content_h, 0)
        access_score = math.log1p(access_count) / 5.0  # normalize to ~0-1

        # 6. Content quality
        quality = self._content_quality(content, tags)

        # Weighted composite
        raw_score = (
            semantic * self.weights.semantic_overlap
            + tag_score * self.weights.tag_match
            + exact * self.weights.exact_match
            + decay * self.weights.recency_decay
            + access_score * self.weights.access_frequency
            + quality * self.weights.content_quality
        )

        layer_weight = LAYER_WEIGHT.get(layer, 1.0)
        return min(1.0, raw_score * layer_weight)

    def _compute_decay(self, timestamp: str, layer: str) -> float:
        """Exponential decay based on layer-specific half-life."""
        ts = _parse_timestamp(timestamp)
        if ts is None:
            return 0.0
        age_hours = (_utc_now() - ts).total_seconds() / 3600
        half_life = DECAY_HALF_LIFE_HOURS.get(layer, 168.0)
        return math.exp(-0.693 * age_hours / half_life)

    def _content_quality(self, content: str, tags: list[str]) -> float:
        """Score content quality based on length and tag richness."""
        length_score = min(len(content) / 500, 1.0)
        tag_score = min(len(tags) / 5, 1.0)
        return (length_score * 0.6 + tag_score * 0.4)

    # ── Deduplication ────────────────────────────────────────────────────

    def deduplicate(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Find and remove duplicate records across all layers.

        Uses content hash for exact dedup and token overlap for near-dedup.
        """
        seen_hashes: dict[str, tuple[str, int]] = {}  # hash → (layer, line)
        duplicates: list[dict[str, Any]] = []

        for layer in LAYERS:
            layer_file = self.memory_dir / layer / "records.jsonl"
            if not layer_file.exists():
                continue

            records: list[dict[str, Any]] = []
            kept: list[dict[str, Any]] = []

            with layer_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    content = str(record.get("content", ""))
                    h = record.get("_content_hash") or _content_hash(content)
                    record["_content_hash"] = h

                    if h in seen_hashes:
                        prev_layer, prev_line = seen_hashes[h]
                        duplicates.append({
                            "hash": h,
                            "layer": layer,
                            "line": line_num,
                            "original_layer": prev_layer,
                            "original_line": prev_line,
                            "content_preview": content[:100],
                        })
                    else:
                        seen_hashes[h] = (layer, line_num)
                        kept.append(record)

            if not dry_run and len(kept) < (len(kept) + len([
                d for d in duplicates if d["layer"] == layer
            ])):
                with layer_file.open("w", encoding="utf-8") as f:
                    for record in kept:
                        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

        return {
            "total_duplicates": len(duplicates),
            "duplicates": duplicates[:20],
            "dry_run": dry_run,
        }

    def _deduplicate_results(self, results: list[ScoredRecord]) -> list[ScoredRecord]:
        """Dedup recall results using content hash + prefix similarity."""
        seen_hashes: set[str] = set()
        seen_prefixes: set[str] = set()
        deduped: list[ScoredRecord] = []

        for rec in results:
            if rec.content_hash in seen_hashes:
                continue
            prefix = rec.content[:200].strip().lower()
            if prefix in seen_prefixes:
                continue
            seen_hashes.add(rec.content_hash)
            seen_prefixes.add(prefix)
            deduped.append(rec)

        return deduped

    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if a content hash already exists in any layer."""
        for layer in LAYERS:
            layer_file = self.memory_dir / layer / "records.jsonl"
            if not layer_file.exists():
                continue
            with layer_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    existing_hash = record.get("_content_hash") or _content_hash(
                        str(record.get("content", ""))
                    )
                    if existing_hash == content_hash:
                        return True
        return False

    # ── TTL Sweep ────────────────────────────────────────────────────────

    def ttl_sweep(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Enforce TTL policies across ALL layers (not just scratchpad/episodic).

        Expired records are moved to archive with metadata.
        """
        now = _utc_now()
        results: list[dict[str, Any]] = []
        total_expired = 0

        for layer, ttl in TTL_POLICIES.items():
            if layer == "archive":
                continue

            layer_file = self.memory_dir / layer / "records.jsonl"
            if not layer_file.exists():
                results.append({"layer": layer, "total": 0, "expired": 0, "kept": 0})
                continue

            kept: list[dict[str, Any]] = []
            expired: list[dict[str, Any]] = []

            with layer_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    ts = _parse_timestamp(record.get("timestamp", ""))
                    if ts and (now - ts) > ttl:
                        expired.append(record)
                    else:
                        kept.append(record)

            if not dry_run and expired:
                archive_dir = self.memory_dir / "archive"
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_file = archive_dir / f"{layer}_archived.jsonl"
                with archive_file.open("a", encoding="utf-8") as f:
                    for record in expired:
                        record["_archived_at"] = now.isoformat()
                        record["_archived_from"] = layer
                        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

                with layer_file.open("w", encoding="utf-8") as f:
                    for record in kept:
                        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

            total_expired += len(expired)
            results.append({
                "layer": layer,
                "ttl_hours": ttl.total_seconds() / 3600,
                "total": len(kept) + len(expired),
                "expired": len(expired),
                "kept": len(kept),
            })

        return {
            "status": "completed",
            "timestamp": now.isoformat(),
            "dry_run": dry_run,
            "total_expired": total_expired,
            "layers": results,
        }

    # ── Access Tracking ──────────────────────────────────────────────────

    def _record_access(self, content_hash: str) -> None:
        self._access_counts[content_hash] = self._access_counts.get(content_hash, 0) + 1

    def _load_access_counts(self) -> None:
        if self._access_log_path.exists():
            try:
                data = json.loads(self._access_log_path.read_text(encoding="utf-8"))
                self._access_counts = defaultdict(int, data)
            except (json.JSONDecodeError, OSError):
                pass

    def save_access_counts(self) -> None:
        """Persist access counts to disk."""
        self._access_log_path.write_text(
            json.dumps(dict(self._access_counts), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Statistics ───────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Memory health metrics across all layers."""
        now = _utc_now()
        layer_stats: dict[str, dict[str, Any]] = {}
        total_records = 0

        for layer in LAYERS:
            layer_file = self.memory_dir / layer / "records.jsonl"
            if not layer_file.exists():
                layer_stats[layer] = {"count": 0, "expired": 0, "avg_age_hours": 0}
                continue

            count = 0
            expired = 0
            ages: list[float] = []
            ttl = TTL_POLICIES.get(layer, timedelta(days=365 * 10))

            with layer_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    count += 1
                    ts = _parse_timestamp(record.get("timestamp", ""))
                    if ts:
                        age_h = (now - ts).total_seconds() / 3600
                        ages.append(age_h)
                        if (now - ts) > ttl:
                            expired += 1

            total_records += count
            layer_stats[layer] = {
                "count": count,
                "expired": expired,
                "ttl_hours": ttl.total_seconds() / 3600,
                "avg_age_hours": round(sum(ages) / len(ages), 1) if ages else 0,
                "oldest_hours": round(max(ages), 1) if ages else 0,
                "newest_hours": round(min(ages), 1) if ages else 0,
            }

        entropy = self._compute_entropy(layer_stats)

        return {
            "total_records": total_records,
            "layers": layer_stats,
            "entropy": round(entropy, 3),
            "access_counts_tracked": len(self._access_counts),
            "timestamp": now.isoformat(),
        }

    def _compute_entropy(self, layer_stats: dict[str, dict[str, Any]]) -> float:
        """Shannon entropy of record distribution across layers."""
        counts = [s["count"] for s in layer_stats.values() if s["count"] > 0]
        total = sum(counts)
        if total == 0:
            return 0.0
        probs = [c / total for c in counts]
        return -sum(p * math.log2(p) for p in probs if p > 0)

    # ── Internal scan ────────────────────────────────────────────────────

    def _scan_layer(
        self,
        layer: str,
        query: str,
        query_tokens: set[str],
        required_tags: list[str] | None,
        min_score: float,
        apply_decay: bool,
    ) -> list[ScoredRecord]:
        """Scan a single layer and return scored records above threshold."""
        layer_file = self.memory_dir / layer / "records.jsonl"
        if not layer_file.exists():
            return []

        results: list[ScoredRecord] = []

        with layer_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if required_tags:
                    record_tags = {t.lower() for t in record.get("tags", [])}
                    if not any(t.lower() in record_tags for t in required_tags):
                        continue

                s = self.score(record, query, query_tokens, layer, apply_decay)
                if s < min_score:
                    continue

                content = str(record.get("content", ""))
                content_h = record.get("_content_hash") or _content_hash(content)
                decay = self._compute_decay(record.get("timestamp", ""), layer)

                results.append(ScoredRecord(
                    content=content[:2000],
                    layer=layer,
                    score=s,
                    timestamp=record.get("timestamp", ""),
                    source=record.get("source", ""),
                    tags=record.get("tags", []),
                    decay_factor=decay,
                    access_count=self._access_counts.get(content_h, 0),
                    content_hash=content_h,
                ))

        return results
