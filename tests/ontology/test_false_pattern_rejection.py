"""Phase 0G — False Pattern Resistance Stress Test.

Verifies that random noise, uncorrelated spikes, and low-signal clusters
are correctly rejected by the promotion pipeline.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.promotion_rules import PROMOTION_RULES, check_promotion_eligibility
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.promotion_engine import PromotionEngine

random.seed(42)

LARGE_SIGNAL_POOL = [
    "cpu_spike", "memory_leak", "disk_latency", "network_jitter",
    "thermal_drift", "fan_mismatch", "power_ripple", "humidity_drop",
    "process_crash", "io_bottleneck", "cache_miss", "gc_pause",
    "thread_deadlock", "socket_timeout", "dns_failure", "cert_expiry",
    "auth_failure", "rate_limit", "queue_overflow", "schema_drift",
]

RANDOM_CONTEXTS = [
    {"cpu_band": "idle", "memory_band": "light"},
    {"cpu_band": "heavy", "memory_band": "saturated"},
    {"cpu_band": "moderate", "memory_band": "idle"},
    {"cpu_band": "light", "memory_band": "heavy"},
    {"cpu_band": "saturated", "memory_band": "moderate"},
]


def _generate_random_episodes(n: int = 50) -> list[EpisodicEntry]:
    """Generate n random, uncorrelated anomaly episodes."""
    base_time = datetime(2025, 3, 1, tzinfo=timezone.utc)
    entries = []
    for i in range(n):
        num_signals = random.randint(1, 3)
        signals = random.sample(LARGE_SIGNAL_POOL, num_signals)
        severity = random.uniform(0.1, 0.4)
        ctx = random.choice(RANDOM_CONTEXTS)
        entries.append(EpisodicEntry(
            entry_id=f"ep-noise-{i:04d}",
            timestamp=base_time + timedelta(hours=random.randint(0, 720)),
            source="random_sensor",
            content=f"Random noise event #{i}",
            tags=["noise", "random"],
            signal_types=signals,
            environmental_context=ctx,
            confidence=severity,
            access_count=1,
        ))
    return entries


def _generate_low_signal_clustered_episodes(n: int = 30) -> list[EpisodicEntry]:
    """Generate n low-signal clustered episodes (same type but low confidence)."""
    base_time = datetime(2025, 3, 1, tzinfo=timezone.utc)
    entries = []
    for i in range(n):
        entries.append(EpisodicEntry(
            entry_id=f"ep-lowsig-{i:04d}",
            timestamp=base_time + timedelta(hours=i),
            source="weak_sensor",
            content=f"Low signal event #{i}",
            tags=["low_signal"],
            signal_types=["thermal_drift"],
            environmental_context={"cpu_band": "idle", "memory_band": "idle"},
            confidence=random.uniform(0.1, 0.49),
            access_count=random.randint(1, 2),
        ))
    return entries


class TestRandomNoiseProducesNoCandidates:
    def test_random_noise_produces_no_candidates(self, promotion_engine):
        """50 random uncorrelated episodes should produce no eligible L2 candidates."""
        entries = _generate_random_episodes(50)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) == 0


class TestUncorrelatedSpikesRejected:
    def test_uncorrelated_spikes_rejected(self, promotion_engine):
        """Random spikes with access_count=1 never meet min_occurrences=3."""
        entries = _generate_random_episodes(50)
        for entry in entries:
            assert entry.access_count < 3
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        for c in candidates:
            assert not c.eligible


class TestLowSignalClustersNotPromoted:
    def test_low_signal_clusters_not_promoted(self, promotion_engine):
        """Low-confidence entries should not be promoted even with same signal type."""
        entries = _generate_low_signal_clustered_episodes(30)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) == 0


class TestBelowThresholdOccurrencesBlocked:
    def test_below_threshold_occurrences_blocked(self, promotion_engine):
        """Entries with access_count < 3 must be blocked."""
        entries = [
            EpisodicEntry(
                entry_id=f"ep-below-occ-{i}",
                timestamp=datetime.now(timezone.utc),
                source="test",
                content="Below threshold",
                tags=["test"],
                signal_types=["thermal_drift"],
                environmental_context={"cpu_band": "heavy"},
                confidence=0.9,
                access_count=2,
            )
            for i in range(10)
        ]
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        for c in candidates:
            assert not c.eligible
            assert any("Occurrences" in r for r in c.blocking_reasons)


class TestLowConfidenceEntriesBlocked:
    def test_low_confidence_entries_blocked(self, promotion_engine):
        """Entries with confidence < 0.7 (L1→L2 threshold) must be blocked."""
        entries = [
            EpisodicEntry(
                entry_id=f"ep-low-conf-{i}",
                timestamp=datetime.now(timezone.utc),
                source="test",
                content="Low confidence",
                tags=["test"],
                signal_types=["thermal_drift"],
                environmental_context={"cpu_band": "heavy"},
                confidence=0.5,
                access_count=5,
            )
            for i in range(10)
        ]
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        for c in candidates:
            assert not c.eligible
            assert any("Confidence" in r for r in c.blocking_reasons)


class TestRejectionRateAbove95Percent:
    def test_rejection_rate_above_95_percent(self, promotion_engine):
        """Combined random + low-signal entries: >95% rejection rate."""
        random_entries = _generate_random_episodes(50)
        low_signal_entries = _generate_low_signal_clustered_episodes(30)
        all_entries = random_entries + low_signal_entries

        candidates = promotion_engine.scan_candidates(all_entries, MemoryLayer.L1_EPISODIC)
        total = len(candidates)
        rejected = len([c for c in candidates if not c.eligible])

        if total > 0:
            rejection_rate = rejected / total
            assert rejection_rate >= 0.95
        else:
            pass


class TestFalsePositiveRateBelow5Percent:
    def test_false_positive_rate_below_5_percent(self, promotion_engine):
        """False positive rate (eligible from noise) must be < 5%."""
        random_entries = _generate_random_episodes(50)
        low_signal_entries = _generate_low_signal_clustered_episodes(30)
        all_entries = random_entries + low_signal_entries

        candidates = promotion_engine.scan_candidates(all_entries, MemoryLayer.L1_EPISODIC)
        total = len(candidates)
        eligible = len([c for c in candidates if c.eligible])

        if total > 0:
            fp_rate = eligible / total
            assert fp_rate < 0.05
        else:
            assert True
