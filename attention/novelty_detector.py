"""
Novelty Detector — Dedicated weak / novel signal detection.

Tracks per-source occurrence counts within a temporal window and computes
a novelty score that habituates (decays) as the same signal recurs.

Integrates conceptually with ``somatic.attention_runtime.anomaly_amplifier``
(which provides a 0.4 first-occurrence boost) but operates at the unified
AttentionSignal level and offers richer habituation curves.
"""

from __future__ import annotations

import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from attention.attention_state import AttentionSignal

logger = logging.getLogger(__name__)


@dataclass
class NoveltyScore:
    """Result of novelty detection for a single signal."""
    signal_id: str
    score: float
    reason: str
    is_first_occurrence: bool
    occurrence_count: int
    habituation_factor: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "score": round(self.score, 4),
            "reason": self.reason,
            "is_first_occurrence": self.is_first_occurrence,
            "occurrence_count": self.occurrence_count,
            "habituation_factor": round(self.habituation_factor, 4),
        }


@dataclass
class _OccurrenceRecord:
    """Internal bookkeeping for a single signal key."""
    count: int = 0
    timestamps: list[float] = field(default_factory=list)


class NoveltyDetector:
    """
    Detects novel signals and computes habituation-aware novelty scores.

    Usage::

        detector = NoveltyDetector()
        score = detector.detect(signal, history=[...])
        if score.is_first_occurrence:
            print("Brand-new signal!")
    """

    def __init__(
        self,
        window_seconds: float = 600.0,
        habituation_half_life: int = 5,
        max_records: int = 2000,
    ) -> None:
        self._window_seconds = window_seconds
        self._habituation_half_life = habituation_half_life
        self._records: dict[str, _OccurrenceRecord] = defaultdict(_OccurrenceRecord)
        self._max_records = max_records

    def detect(
        self,
        signal: AttentionSignal,
        history: list[AttentionSignal] | None = None,
    ) -> NoveltyScore:
        """
        Compute a novelty score for *signal*.

        If *history* is supplied it is scanned for matching occurrences inside
        the temporal window; otherwise the detector relies on its internal
        occurrence ledger.
        """
        sig_key = f"{signal.source_domain}:{signal.signal_type}:{signal.metadata.get('sub_type', '')}"
        now = time.time()

        self._prune_old(sig_key, now)

        record = self._records[sig_key]
        record.count += 1
        record.timestamps.append(now)

        window_count = record.count
        if history:
            cutoff = now - self._window_seconds
            window_count = sum(
                1 for s in history
                if self._signal_key(s) == sig_key
                and s.timestamp.timestamp() >= cutoff
            ) + 1  # include current

        is_first = window_count <= 1
        habituation = self._habituation(window_count)
        novelty = 1.0 - habituation

        reason = self._explain(is_first, window_count, novelty)

        score = NoveltyScore(
            signal_id=signal.signal_id,
            score=novelty,
            reason=reason,
            is_first_occurrence=is_first,
            occurrence_count=window_count,
            habituation_factor=habituation,
        )

        logger.debug(
            "Novelty for %s [%s]: %.3f (count=%d, hab=%.3f)",
            signal.signal_id[:8], sig_key, novelty, window_count, habituation,
        )

        self._maybe_evict()
        return score

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _habituation(self, count: int) -> float:
        """
        Compute habituation factor (0.0 = fully novel, 1.0 = fully habituated).

        Uses a logarithmic curve with configurable half-life (number of
        occurrences at which habituation reaches 0.5).
        """
        if count <= 1:
            return 0.0
        hl = max(self._habituation_half_life, 2)
        return min(1.0, math.log2(count) / math.log2(hl * 2))

    def _prune_old(self, sig_key: str, now: float) -> None:
        """Remove timestamps outside the window."""
        record = self._records[sig_key]
        cutoff = now - self._window_seconds
        fresh = [t for t in record.timestamps if t >= cutoff]
        record.timestamps = fresh
        record.count = len(fresh)

    def _maybe_evict(self) -> None:
        """Evict least-recently-used keys when the ledger grows too large."""
        if len(self._records) <= self._max_records:
            return
        by_last_ts = sorted(
            self._records.items(),
            key=lambda kv: kv[1].timestamps[-1] if kv[1].timestamps else 0.0,
        )
        to_remove = len(self._records) - self._max_records
        for key, _ in by_last_ts[:to_remove]:
            del self._records[key]

    @staticmethod
    def _signal_key(signal: AttentionSignal) -> str:
        return f"{signal.source_domain}:{signal.signal_type}:{signal.metadata.get('sub_type', '')}"

    @staticmethod
    def _explain(is_first: bool, count: int, score: float) -> str:
        if is_first:
            return "First occurrence — maximum novelty"
        if score > 0.7:
            return f"Rare signal (seen {count} times) — high novelty"
        if score > 0.3:
            return f"Moderately familiar (seen {count} times)"
        return f"Well-known pattern (seen {count} times) — habituated"
