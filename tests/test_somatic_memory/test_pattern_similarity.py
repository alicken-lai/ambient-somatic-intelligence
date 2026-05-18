"""Tests for memory.somatic.pattern_similarity — Episode similarity, clustering."""

from __future__ import annotations

from datetime import datetime, timezone

from memory.somatic.sensor_episode_store import SensorEpisode
from memory.somatic.pattern_similarity import PatternSimilarity


def _make_episode(
    episode_id: str,
    signal_types: list[str],
    severity: float = 0.5,
    duration_ms: float = 1000.0,
    env_vector: list[float] | None = None,
    fingerprint: str = "",
) -> SensorEpisode:
    return SensorEpisode(
        episode_id=episode_id,
        timestamp=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        severity_peak=severity,
        signal_types=signal_types,
        environmental_signature={
            "cpu_band": "moderate",
            "memory_band": "light",
            "disk_band": "idle",
            "load_band": "light",
            "process_band": "normal",
            "composite_vector": env_vector or [0.5, 0.4, 0.3, 0.2, 0.3],
        },
        fingerprint=fingerprint,
    )


def test_identical_episodes_similar() -> None:
    """Same episode compared to itself yields similarity ~1.0."""
    sim = PatternSimilarity()
    ep = _make_episode("ep1", ["cpu_spike"], severity=0.8)

    result = sim.episode_similarity(ep, ep)
    assert result.score >= 0.9
    assert result.confidence > 0


def test_different_episodes_dissimilar() -> None:
    """Very different episodes yield low similarity."""
    sim = PatternSimilarity()
    ep_a = _make_episode(
        "ep-a",
        ["cpu_spike"],
        severity=0.9,
        duration_ms=100.0,
        env_vector=[0.9, 0.8, 0.7, 0.8, 0.7],
    )
    ep_b = _make_episode(
        "ep-b",
        ["disk_io", "network_error"],
        severity=0.1,
        duration_ms=50000.0,
        env_vector=[0.1, 0.1, 0.1, 0.1, 0.1],
    )

    result = sim.episode_similarity(ep_a, ep_b)
    assert result.score < 0.5


def test_similarity_factors() -> None:
    """All expected factors are present in the result."""
    sim = PatternSimilarity()
    ep_a = _make_episode("fa", ["cpu_spike"])
    ep_b = _make_episode("fb", ["cpu_spike", "mem_pressure"])

    result = sim.episode_similarity(ep_a, ep_b)
    assert "signal_type_overlap" in result.factors
    assert "env_distance" in result.factors
    assert "severity_similarity" in result.factors
    assert "temporal_similarity" in result.factors
    assert "fingerprint_match" in result.factors
    assert result.explanation


def test_clustering() -> None:
    """Similar episodes are grouped into clusters."""
    sim = PatternSimilarity()

    episodes = [
        _make_episode("c1", ["cpu_spike"], severity=0.8),
        _make_episode("c2", ["cpu_spike"], severity=0.75),
        _make_episode("c3", ["cpu_spike"], severity=0.82),
        _make_episode("c4", ["disk_io", "network_error"], severity=0.2,
                       env_vector=[0.1, 0.1, 0.9, 0.1, 0.1]),
    ]

    clusters = sim.find_clusters(episodes, threshold=0.5)
    assert len(clusters) >= 1

    largest = max(clusters, key=lambda c: len(c.episode_ids))
    assert len(largest.episode_ids) >= 2
    assert largest.avg_similarity > 0
    assert largest.centroid_episode_id
