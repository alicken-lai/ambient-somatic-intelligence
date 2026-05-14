"""Tests for memory.somatic.sensor_episode_store — Store, query, persistence, eviction."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from memory.somatic.sensor_episode_store import (
    EpisodeFilter,
    SensorEpisode,
    SomaticEpisodeStore,
)


def _make_episode(
    episode_id: str = "ep-001",
    severity: float = 0.5,
    signal_types: list[str] | None = None,
    ts_offset_minutes: int = 0,
) -> SensorEpisode:
    ts = datetime.now(timezone.utc) - timedelta(minutes=ts_offset_minutes)
    return SensorEpisode(
        episode_id=episode_id,
        timestamp=ts,
        duration_ms=1000.0,
        severity_peak=severity,
        signal_types=signal_types or ["cpu_spike"],
        environmental_signature={
            "cpu_band": "heavy",
            "memory_band": "moderate",
            "disk_band": "idle",
            "load_band": "moderate",
            "process_band": "normal",
            "composite_vector": [0.7, 0.5, 0.3, 0.4, 0.3],
        },
        source_signals=[{"type": "cpu_spike", "value": 0.8}],
    )


def test_store_and_retrieve(tmp_dir: Path) -> None:
    """Store an episode and retrieve it by id."""
    store = SomaticEpisodeStore(path=tmp_dir / "episodes.jsonl", max_episodes=100)
    ep = _make_episode("ep-store-001")
    eid = store.store(ep)

    assert eid == "ep-store-001"
    retrieved = store.get(eid)
    assert retrieved is not None
    assert retrieved.episode_id == "ep-store-001"
    assert retrieved.severity_peak == 0.5


def test_query_by_severity(tmp_dir: Path) -> None:
    """Filter episodes by min_severity."""
    store = SomaticEpisodeStore(path=tmp_dir / "episodes.jsonl", max_episodes=100)
    store.store(_make_episode("ep-low", severity=0.2))
    store.store(_make_episode("ep-mid", severity=0.5))
    store.store(_make_episode("ep-high", severity=0.9))

    results = store.query(EpisodeFilter(min_severity=0.6))
    assert len(results) == 1
    assert results[0].episode_id == "ep-high"


def test_query_by_time_range(tmp_dir: Path) -> None:
    """Filter episodes by timestamp range."""
    store = SomaticEpisodeStore(path=tmp_dir / "episodes.jsonl", max_episodes=100)
    store.store(_make_episode("ep-old", ts_offset_minutes=120))
    store.store(_make_episode("ep-recent", ts_offset_minutes=5))

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    results = store.query(EpisodeFilter(time_start=cutoff))
    assert len(results) == 1
    assert results[0].episode_id == "ep-recent"


def test_persistence_roundtrip(tmp_dir: Path) -> None:
    """Store, reload from JSONL, verify episodes survive restart."""
    path = tmp_dir / "persist.jsonl"
    store1 = SomaticEpisodeStore(path=path, max_episodes=100)
    store1.store(_make_episode("ep-persist-1", severity=0.7))
    store1.store(_make_episode("ep-persist-2", severity=0.3))

    store2 = SomaticEpisodeStore(path=path, max_episodes=100)
    assert store2.count == 2
    assert store2.get("ep-persist-1") is not None
    assert store2.get("ep-persist-2") is not None


def test_eviction(tmp_dir: Path) -> None:
    """Exceeding max_episodes evicts the oldest entries."""
    store = SomaticEpisodeStore(path=tmp_dir / "episodes.jsonl", max_episodes=3)
    store.store(_make_episode("ep-1", ts_offset_minutes=40))
    store.store(_make_episode("ep-2", ts_offset_minutes=30))
    store.store(_make_episode("ep-3", ts_offset_minutes=20))
    store.store(_make_episode("ep-4", ts_offset_minutes=10))

    assert store.count == 3
    assert store.get("ep-1") is None
    assert store.get("ep-4") is not None


def test_find_similar(tmp_dir: Path) -> None:
    """Similar episodes are found by similarity search."""
    store = SomaticEpisodeStore(path=tmp_dir / "episodes.jsonl", max_episodes=100)

    ep1 = _make_episode("ep-sim-1", severity=0.8, signal_types=["cpu_spike"])
    ep2 = _make_episode("ep-sim-2", severity=0.75, signal_types=["cpu_spike"])
    ep3 = _make_episode(
        "ep-diff", severity=0.2, signal_types=["disk_io"]
    )

    store.store(ep1)
    store.store(ep2)
    store.store(ep3)

    similar = store.find_similar(ep1, threshold=0.3)
    similar_ids = [ep.episode_id for ep, _ in similar]
    assert "ep-sim-2" in similar_ids


def test_recent(tmp_dir: Path) -> None:
    """recent() returns episodes in reverse chronological order."""
    store = SomaticEpisodeStore(path=tmp_dir / "episodes.jsonl", max_episodes=100)
    store.store(_make_episode("ep-a", ts_offset_minutes=10))
    store.store(_make_episode("ep-b", ts_offset_minutes=5))
    store.store(_make_episode("ep-c", ts_offset_minutes=1))

    recent = store.recent(2)
    assert len(recent) == 2
    assert recent[0].episode_id == "ep-c"
