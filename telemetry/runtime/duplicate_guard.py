"""
Duplicate Guard — Prevents duplicate telemetry records from overlapping triggers.

When both launchd and the in-process SamplingScheduler fire for the same
source within a short window, this guard detects and suppresses the
duplicate using a sliding content-hash window.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_WINDOW_SECONDS = 30.0
_DEFAULT_NEAR_DUPLICATE_SECONDS = 10.0
_DEFAULT_MAX_HASHES = 10_000


@dataclass
class DeduplicationResult:
    """Outcome of a deduplication check."""
    is_duplicate: bool
    is_near_duplicate: bool
    source_name: str
    content_hash: str
    timestamp: float
    matched_hash: Optional[str] = None
    matched_timestamp: Optional[float] = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_duplicate": self.is_duplicate,
            "is_near_duplicate": self.is_near_duplicate,
            "source_name": self.source_name,
            "content_hash": self.content_hash,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "matched_hash": self.matched_hash,
            "matched_timestamp": (
                datetime.fromtimestamp(self.matched_timestamp, tz=timezone.utc).isoformat()
                if self.matched_timestamp else None
            ),
            "reason": self.reason,
        }


@dataclass
class DeduplicationStats:
    """Aggregate deduplication statistics."""
    total_checked: int = 0
    exact_duplicates: int = 0
    near_duplicates: int = 0
    unique_records: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_checked": self.total_checked,
            "exact_duplicates": self.exact_duplicates,
            "near_duplicates": self.near_duplicates,
            "unique_records": self.unique_records,
            "duplicate_rate": (
                round((self.exact_duplicates + self.near_duplicates) / self.total_checked, 4)
                if self.total_checked > 0 else 0.0
            ),
        }


class DuplicateGuard:
    """Prevents duplicate telemetry records from overlapping sampling triggers.

    Uses a sliding deduplication window with configurable tolerance.

    Parameters
    ----------
    window_seconds:
        Time window within which content hashes are compared.
    near_duplicate_seconds:
        Records from the same source within this many seconds of each
        other are flagged as near-duplicates even if content differs.
    max_hashes:
        Maximum number of hashes to keep in the sliding window.
    clock_fn:
        Override for deterministic testing / replay.
    """

    def __init__(
        self,
        window_seconds: float = _DEFAULT_WINDOW_SECONDS,
        near_duplicate_seconds: float = _DEFAULT_NEAR_DUPLICATE_SECONDS,
        max_hashes: int = _DEFAULT_MAX_HASHES,
        clock_fn=None,
    ):
        self._window = window_seconds
        self._near_dup_window = near_duplicate_seconds
        self._max_hashes = max_hashes
        self._clock = clock_fn or time.time

        self._hash_window: OrderedDict[str, _HashEntry] = OrderedDict()
        self._source_timestamps: dict[str, float] = {}
        self._stats = DeduplicationStats()
        self._deduplicated_log: list[dict[str, Any]] = []
        self._max_log = 2000

    # ── Core API ──────────────────────────────────────────────────────

    def check(
        self,
        source_name: str,
        data: dict[str, Any],
        timestamp: float | None = None,
    ) -> DeduplicationResult:
        """Check if a record is a duplicate.

        Call this before persisting a telemetry sample.  If the result
        has ``is_duplicate=True`` or ``is_near_duplicate=True``, the
        record should be discarded.
        """
        now = timestamp if timestamp is not None else self._clock()
        content_hash = self._hash_content(source_name, data)
        self._stats.total_checked += 1

        self._evict_expired(now)

        if content_hash in self._hash_window:
            entry = self._hash_window[content_hash]
            result = DeduplicationResult(
                is_duplicate=True,
                is_near_duplicate=False,
                source_name=source_name,
                content_hash=content_hash,
                timestamp=now,
                matched_hash=content_hash,
                matched_timestamp=entry.timestamp,
                reason="Exact content hash match within dedup window",
            )
            self._stats.exact_duplicates += 1
            self._log_dedup(result)
            logger.debug(
                "Exact duplicate detected for '%s' (hash=%s)",
                source_name,
                content_hash[:12],
            )
            return result

        last_ts = self._source_timestamps.get(source_name)
        if last_ts is not None and (now - last_ts) < self._near_dup_window:
            result = DeduplicationResult(
                is_duplicate=False,
                is_near_duplicate=True,
                source_name=source_name,
                content_hash=content_hash,
                timestamp=now,
                matched_timestamp=last_ts,
                reason=(
                    f"Same source '{source_name}' sampled {now - last_ts:.1f}s ago "
                    f"(threshold={self._near_dup_window}s)"
                ),
            )
            self._stats.near_duplicates += 1
            self._log_dedup(result)
            logger.debug(
                "Near-duplicate detected for '%s': gap=%.1fs",
                source_name,
                now - last_ts,
            )
            return result

        self._hash_window[content_hash] = _HashEntry(
            content_hash=content_hash,
            source_name=source_name,
            timestamp=now,
        )
        self._source_timestamps[source_name] = now
        self._stats.unique_records += 1

        self._enforce_max_hashes()

        return DeduplicationResult(
            is_duplicate=False,
            is_near_duplicate=False,
            source_name=source_name,
            content_hash=content_hash,
            timestamp=now,
        )

    def accept(
        self,
        source_name: str,
        data: dict[str, Any],
        timestamp: float | None = None,
    ) -> bool:
        """Convenience: returns True if the record is NOT a duplicate."""
        result = self.check(source_name, data, timestamp)
        return not result.is_duplicate and not result.is_near_duplicate

    # ── Stats & Reports ───────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        return self._stats.to_dict()

    def recent_deduplication_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self._deduplicated_log[-limit:]))

    def window_size(self) -> int:
        return len(self._hash_window)

    def reset(self) -> None:
        """Clear all state (for testing)."""
        self._hash_window.clear()
        self._source_timestamps.clear()
        self._stats = DeduplicationStats()
        self._deduplicated_log.clear()

    # ── Internals ─────────────────────────────────────────────────────

    @staticmethod
    def _hash_content(source_name: str, data: dict[str, Any]) -> str:
        canonical = json.dumps(
            {"source": source_name, "data": data},
            sort_keys=True,
            ensure_ascii=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _evict_expired(self, now: float) -> None:
        cutoff = now - self._window
        expired_keys = [
            k for k, entry in self._hash_window.items()
            if entry.timestamp < cutoff
        ]
        for k in expired_keys:
            del self._hash_window[k]

    def _enforce_max_hashes(self) -> None:
        while len(self._hash_window) > self._max_hashes:
            self._hash_window.popitem(last=False)

    def _log_dedup(self, result: DeduplicationResult) -> None:
        self._deduplicated_log.append(result.to_dict())
        if len(self._deduplicated_log) > self._max_log:
            self._deduplicated_log = self._deduplicated_log[-self._max_log:]


@dataclass
class _HashEntry:
    """Internal hash-window entry."""
    content_hash: str
    source_name: str
    timestamp: float
