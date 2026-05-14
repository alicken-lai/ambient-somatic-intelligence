"""Caching layer for memory retrieval to avoid repeated full scans."""
from __future__ import annotations

import hashlib
import logging
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    max_entries: int = 200
    ttl_seconds: float = 300.0
    max_memory_mb: float = 50.0
    enable_fuzzy_match: bool = True
    fuzzy_threshold: float = 0.85


@dataclass
class CacheEntry:
    cache_key: str
    query: str
    max_results: int
    layers: list[str] | None
    results: list[dict]
    created_at: float
    last_accessed: float
    hit_count: int
    original_scan_ms: float
    entry_size_bytes: int


@dataclass
class CacheResult:
    hit: bool
    results: list[dict] | None
    cache_key: str
    saved_ms: float
    freshness: float


@dataclass
class CacheStats:
    total_entries: int
    max_entries: int
    hit_count: int
    miss_count: int
    hit_rate: float
    total_saved_ms: float
    avg_saved_ms: float
    memory_usage_bytes: int
    eviction_count: int


class RecallCache:
    def __init__(self, config: CacheConfig | None = None) -> None:
        self._config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0
        self._total_saved_ms = 0.0
        self._eviction_count = 0
        self._total_memory_bytes = 0

    def get(
        self,
        query: str,
        max_results: int,
        layers: list[str] | None = None,
    ) -> CacheResult:
        key = self._compute_cache_key(query, max_results, layers)

        entry = self._cache.get(key)
        if entry and not self._is_expired(entry):
            self._cache.move_to_end(key)
            entry.hit_count += 1
            entry.last_accessed = time.time()
            self._hit_count += 1
            self._total_saved_ms += entry.original_scan_ms
            freshness = self._compute_freshness(entry)
            return CacheResult(
                hit=True,
                results=entry.results,
                cache_key=key,
                saved_ms=entry.original_scan_ms,
                freshness=freshness,
            )

        if entry:
            self._remove_entry(key)

        if self._config.enable_fuzzy_match:
            fuzzy_result = self._fuzzy_lookup(query, max_results, layers)
            if fuzzy_result:
                return fuzzy_result

        self._miss_count += 1
        return CacheResult(
            hit=False, results=None, cache_key=key, saved_ms=0.0, freshness=0.0
        )

    def put(
        self,
        query: str,
        max_results: int,
        layers: list[str] | None,
        results: list[dict],
        scan_ms: float,
    ) -> None:
        key = self._compute_cache_key(query, max_results, layers)
        entry_size = self._estimate_size(results)

        if key in self._cache:
            self._remove_entry(key)

        now = time.time()
        entry = CacheEntry(
            cache_key=key,
            query=query,
            max_results=max_results,
            layers=layers,
            results=results,
            created_at=now,
            last_accessed=now,
            hit_count=0,
            original_scan_ms=scan_ms,
            entry_size_bytes=entry_size,
        )

        self._cache[key] = entry
        self._total_memory_bytes += entry_size
        self._evict_if_needed()

    def invalidate(self, layer: str | None = None) -> int:
        if layer is None:
            count = len(self._cache)
            self._cache.clear()
            self._total_memory_bytes = 0
            return count

        to_remove: list[str] = []
        for key, entry in self._cache.items():
            if entry.layers is None or layer in entry.layers:
                to_remove.append(key)

        for key in to_remove:
            self._remove_entry(key)
        return len(to_remove)

    def get_stats(self) -> CacheStats:
        total_lookups = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_lookups if total_lookups > 0 else 0.0
        avg_saved = (
            self._total_saved_ms / self._hit_count if self._hit_count > 0 else 0.0
        )

        return CacheStats(
            total_entries=len(self._cache),
            max_entries=self._config.max_entries,
            hit_count=self._hit_count,
            miss_count=self._miss_count,
            hit_rate=hit_rate,
            total_saved_ms=self._total_saved_ms,
            avg_saved_ms=avg_saved,
            memory_usage_bytes=self._total_memory_bytes,
            eviction_count=self._eviction_count,
        )

    def _compute_cache_key(
        self, query: str, max_results: int, layers: list[str] | None
    ) -> str:
        normalized = query.strip().lower()
        layer_key = ",".join(sorted(layers)) if layers else ""
        raw = f"{normalized}|{max_results}|{layer_key}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _is_expired(self, entry: CacheEntry) -> bool:
        return (time.time() - entry.created_at) > self._config.ttl_seconds

    def _evict_if_needed(self) -> int:
        evicted = 0
        while len(self._cache) > self._config.max_entries:
            key, _ = self._cache.popitem(last=False)
            evicted += 1

        max_bytes = int(self._config.max_memory_mb * 1024 * 1024)
        while self._total_memory_bytes > max_bytes and self._cache:
            key, entry = self._cache.popitem(last=False)
            self._total_memory_bytes -= entry.entry_size_bytes
            evicted += 1

        self._eviction_count += evicted
        return evicted

    def _remove_entry(self, key: str) -> None:
        entry = self._cache.pop(key, None)
        if entry:
            self._total_memory_bytes -= entry.entry_size_bytes

    def _fuzzy_lookup(
        self,
        query: str,
        max_results: int,
        layers: list[str] | None,
    ) -> CacheResult | None:
        query_tokens = set(query.strip().lower().split())
        if not query_tokens:
            return None

        best_entry: CacheEntry | None = None
        best_score = 0.0

        for entry in self._cache.values():
            if self._is_expired(entry):
                continue
            if entry.max_results < max_results:
                continue
            entry_tokens = set(entry.query.strip().lower().split())
            if not entry_tokens:
                continue
            intersection = query_tokens & entry_tokens
            union = query_tokens | entry_tokens
            score = len(intersection) / len(union)
            if score >= self._config.fuzzy_threshold and score > best_score:
                best_score = score
                best_entry = entry

        if best_entry:
            best_entry.hit_count += 1
            best_entry.last_accessed = time.time()
            self._hit_count += 1
            self._total_saved_ms += best_entry.original_scan_ms
            self._cache.move_to_end(best_entry.cache_key)
            return CacheResult(
                hit=True,
                results=best_entry.results[:max_results],
                cache_key=best_entry.cache_key,
                saved_ms=best_entry.original_scan_ms,
                freshness=self._compute_freshness(best_entry),
            )
        return None

    def _compute_freshness(self, entry: CacheEntry) -> float:
        age = time.time() - entry.created_at
        ttl = self._config.ttl_seconds
        if ttl <= 0:
            return 1.0
        return max(0.0, 1.0 - (age / ttl))

    @staticmethod
    def _estimate_size(results: list[dict]) -> int:
        try:
            return sys.getsizeof(results) + sum(
                sys.getsizeof(r) for r in results
            )
        except Exception:
            return len(results) * 512
