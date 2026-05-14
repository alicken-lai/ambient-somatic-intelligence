"""
Somatic Episode Store — Persistent storage for environmental episodes.

Bridges the gap between in-memory somatic signals (which are lost on restart)
and the memory kernel by providing an append-only JSONL store with:
  - SensorEpisode: rich dataclass capturing an entire somatic event window
  - SomaticEpisodeStore: query, index, similarity search, and eviction
  - EpisodeFilter: structured query predicates

Episodes are persisted to ``memory/somatic/episodes.jsonl`` and indexed
in-memory on startup for sub-millisecond lookups.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from memory.somatic.environmental_signature import EnvironmentalSignature
from memory.somatic.anomaly_fingerprint import AnomalyFingerprint

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
DEFAULT_EPISODES_PATH = AMBIENT_ROOT / "memory" / "somatic" / "episodes.jsonl"
DEFAULT_MAX_EPISODES = 10_000


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return _utc_now()


def _opt_parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    return _parse_dt(val)


# ── SensorEpisode ─────────────────────────────────────────────────────────


@dataclass
class SensorEpisode:
    """A bounded somatic event — from first signal to resolution/decay."""

    episode_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: datetime = field(default_factory=_utc_now)
    end_timestamp: Optional[datetime] = None
    duration_ms: float = 0.0
    source_signals: list[dict[str, Any]] = field(default_factory=list)
    environmental_signature: dict[str, Any] = field(default_factory=dict)
    preceding_events: list[str] = field(default_factory=list)
    anomaly_score: float = 0.0
    attention_score: float = 0.0
    severity_peak: float = 0.0
    signal_types: list[str] = field(default_factory=list)
    correlation_rules_fired: list[str] = field(default_factory=list)
    outcome: Optional[str] = None
    linked_memory_ids: list[str] = field(default_factory=list)
    similarity_clusters: list[str] = field(default_factory=list)
    governance_notes: list[str] = field(default_factory=list)
    fingerprint: str = ""

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "timestamp": self.timestamp.isoformat(),
            "end_timestamp": self.end_timestamp.isoformat() if self.end_timestamp else None,
            "duration_ms": self.duration_ms,
            "source_signals": self.source_signals,
            "environmental_signature": self.environmental_signature,
            "preceding_events": self.preceding_events,
            "anomaly_score": round(self.anomaly_score, 6),
            "attention_score": round(self.attention_score, 6),
            "severity_peak": round(self.severity_peak, 6),
            "signal_types": self.signal_types,
            "correlation_rules_fired": self.correlation_rules_fired,
            "outcome": self.outcome,
            "linked_memory_ids": self.linked_memory_ids,
            "similarity_clusters": self.similarity_clusters,
            "governance_notes": self.governance_notes,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SensorEpisode:
        return cls(
            episode_id=data.get("episode_id", uuid.uuid4().hex[:16]),
            timestamp=_parse_dt(data.get("timestamp")),
            end_timestamp=_opt_parse_dt(data.get("end_timestamp")),
            duration_ms=float(data.get("duration_ms", 0.0)),
            source_signals=data.get("source_signals", []),
            environmental_signature=data.get("environmental_signature", {}),
            preceding_events=data.get("preceding_events", []),
            anomaly_score=float(data.get("anomaly_score", 0.0)),
            attention_score=float(data.get("attention_score", 0.0)),
            severity_peak=float(data.get("severity_peak", 0.0)),
            signal_types=data.get("signal_types", []),
            correlation_rules_fired=data.get("correlation_rules_fired", []),
            outcome=data.get("outcome"),
            linked_memory_ids=data.get("linked_memory_ids", []),
            similarity_clusters=data.get("similarity_clusters", []),
            governance_notes=data.get("governance_notes", []),
            fingerprint=data.get("fingerprint", ""),
        )


# ── EpisodeFilter ─────────────────────────────────────────────────────────


@dataclass
class EpisodeFilter:
    """Structured query predicates for episode retrieval."""

    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    signal_types: Optional[list[str]] = None
    min_severity: float = 0.0
    max_results: int = 50
    fingerprint_match: Optional[str] = None


# ── SomaticEpisodeStore ───────────────────────────────────────────────────


class SomaticEpisodeStore:
    """
    Persistent store for somatic episodes backed by a JSONL file.

    Maintains an in-memory index (dict by episode_id and deque ordered by
    timestamp) that is populated on construction by scanning the JSONL file.
    Oldest episodes are evicted when ``max_episodes`` is exceeded.
    """

    def __init__(
        self,
        path: Path | str | None = None,
        max_episodes: int = DEFAULT_MAX_EPISODES,
    ):
        self._path = Path(path) if path else DEFAULT_EPISODES_PATH
        self._max_episodes = max_episodes
        self._index: dict[str, SensorEpisode] = {}
        self._ordered: list[str] = []
        self._load()

    # ── Public API ────────────────────────────────────────────────────

    def store(self, episode: SensorEpisode) -> str:
        """Persist an episode and return its episode_id."""
        self._index[episode.episode_id] = episode
        self._ordered.append(episode.episode_id)
        self._append_to_disk(episode)
        self._evict_if_needed()
        logger.debug("Stored episode %s (total=%d)", episode.episode_id, len(self._index))
        return episode.episode_id

    def get(self, episode_id: str) -> Optional[SensorEpisode]:
        return self._index.get(episode_id)

    def query(self, filters: EpisodeFilter) -> list[SensorEpisode]:
        results: list[SensorEpisode] = []
        for eid in reversed(self._ordered):
            ep = self._index.get(eid)
            if ep is None:
                continue
            if not self._matches(ep, filters):
                continue
            results.append(ep)
            if len(results) >= filters.max_results:
                break
        return results

    def recent(self, n: int = 10) -> list[SensorEpisode]:
        ids = self._ordered[-n:] if n > 0 else []
        out: list[SensorEpisode] = []
        for eid in reversed(ids):
            ep = self._index.get(eid)
            if ep is not None:
                out.append(ep)
        return out

    def find_similar(
        self,
        episode: SensorEpisode,
        threshold: float = 0.5,
    ) -> list[tuple[SensorEpisode, float]]:
        """Find episodes similar to the given one.

        Delegates to PatternSimilarity lazily to avoid a circular import
        at module level. Returns (episode, score) pairs above *threshold*,
        sorted by descending similarity.
        """
        from memory.somatic.pattern_similarity import PatternSimilarity

        sim = PatternSimilarity()
        matches: list[tuple[SensorEpisode, float]] = []
        for ep in self._index.values():
            if ep.episode_id == episode.episode_id:
                continue
            result = sim.episode_similarity(episode, ep)
            if result.score >= threshold:
                matches.append((ep, result.score))
        matches.sort(key=lambda t: t[1], reverse=True)
        return matches

    def link_outcome(self, episode_id: str, outcome: str) -> bool:
        ep = self._index.get(episode_id)
        if ep is None:
            return False
        ep.outcome = outcome
        self._rewrite_disk()
        return True

    @property
    def count(self) -> int:
        return len(self._index)

    # ── Filtering ─────────────────────────────────────────────────────

    @staticmethod
    def _matches(ep: SensorEpisode, f: EpisodeFilter) -> bool:
        if f.time_start and ep.timestamp < f.time_start:
            return False
        if f.time_end and ep.timestamp > f.time_end:
            return False
        if f.signal_types:
            if not set(f.signal_types) & set(ep.signal_types):
                return False
        if ep.severity_peak < f.min_severity:
            return False
        if f.fingerprint_match and ep.fingerprint != f.fingerprint_match:
            return False
        return True

    # ── Persistence helpers ───────────────────────────────────────────

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        ep = SensorEpisode.from_dict(data)
                        self._index[ep.episode_id] = ep
                        self._ordered.append(ep.episode_id)
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.warning("Skipped malformed episode line: %s", exc)
        except OSError as exc:
            logger.error("Failed to load episodes from %s: %s", self._path, exc)

    def _append_to_disk(self, episode: SensorEpisode) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(episode.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            logger.error("Failed to append episode %s: %s", episode.episode_id, exc)

    def _rewrite_disk(self) -> None:
        """Full rewrite — used only for rare mutations like link_outcome."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._path.open("w", encoding="utf-8") as fh:
                for eid in self._ordered:
                    ep = self._index.get(eid)
                    if ep is not None:
                        fh.write(json.dumps(ep.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            logger.error("Failed to rewrite episodes file: %s", exc)

    def _evict_if_needed(self) -> None:
        while len(self._index) > self._max_episodes:
            oldest_id = self._ordered.pop(0)
            evicted = self._index.pop(oldest_id, None)
            if evicted:
                logger.debug("Evicted oldest episode %s", oldest_id)
        if len(self._ordered) > self._max_episodes:
            self._rewrite_disk()
