"""Tests for the somatic→ontology bridge (Phase 3)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest

from memory.somatic.ontology_bridge import (
    OntologyMapping,
    PromotionCandidate,
    SomaticOntologyBridge,
)


# ── Lightweight stubs ─────────────────────────────────────────────────────


@dataclass
class _FakeEpisode:
    episode_id: str = "ep-001"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signal_types: list[str] = field(default_factory=lambda: ["cpu_spike"])
    severity_peak: float = 0.7


@dataclass
class _FakeFingerprint:
    fingerprint_id: str = "fp-001"
    occurrence_count: int = 1
    severity_band: str = "high"


@dataclass
class _FakeCluster:
    cluster_id: str = "cl-001"
    episode_ids: list[str] = field(default_factory=lambda: ["ep-1", "ep-2", "ep-3", "ep-4", "ep-5"])
    avg_similarity: float = 0.8
    centroid_episode_id: str = "ep-1"
    pattern_description: str = "Cluster of 5 episodes: cpu_spike+memory_pressure"


@dataclass
class _FakePrecursor:
    pattern_id: str = "pr-001"
    confidence: float = 0.9
    support_count: int = 5
    avg_lead_time_seconds: float = 120.0
    target_event_type: str = "cpu_spike"
    precursor_signals: list[str] = field(default_factory=lambda: ["disk_io", "memory_rise"])


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def bridge(tmp_path: Path) -> SomaticOntologyBridge:
    return SomaticOntologyBridge(mappings_path=str(tmp_path / "mappings.jsonl"))


# ── L1 mapping ────────────────────────────────────────────────────────────


class TestMapEpisodeToL1:

    def test_always_maps_to_l1(self, bridge: SomaticOntologyBridge) -> None:
        mapping = bridge.map_episode_to_l1(_FakeEpisode())
        assert mapping.target_layer == 1
        assert mapping.source_type == "episode"
        assert mapping.confidence == 1.0

    def test_entry_id_prefix(self, bridge: SomaticOntologyBridge) -> None:
        mapping = bridge.map_episode_to_l1(_FakeEpisode(episode_id="ep-xyz"))
        assert mapping.target_entry_id.startswith("L1-")


# ── L2 mapping ────────────────────────────────────────────────────────────


class TestMapFingerprintToL2:

    def test_requires_min_occurrences(self, bridge: SomaticOntologyBridge) -> None:
        fp = _FakeFingerprint(occurrence_count=2)
        assert bridge.map_fingerprint_to_l2(fp, min_occurrences=3) is None

    def test_maps_when_threshold_met(self, bridge: SomaticOntologyBridge) -> None:
        fp = _FakeFingerprint(occurrence_count=5)
        mapping = bridge.map_fingerprint_to_l2(fp, min_occurrences=3)
        assert mapping is not None
        assert mapping.target_layer == 2
        assert mapping.source_type == "fingerprint"

    def test_confidence_capped(self, bridge: SomaticOntologyBridge) -> None:
        fp = _FakeFingerprint(occurrence_count=100)
        mapping = bridge.map_fingerprint_to_l2(fp, min_occurrences=3)
        assert mapping is not None
        assert mapping.confidence <= 0.99


# ── L3 mapping ────────────────────────────────────────────────────────────


class TestMapClusterToL3:

    def test_requires_min_episodes(self, bridge: SomaticOntologyBridge) -> None:
        cluster = _FakeCluster(episode_ids=["e1", "e2"])
        assert bridge.map_cluster_to_l3(cluster, min_episodes=5) is None

    def test_requires_min_similarity(self, bridge: SomaticOntologyBridge) -> None:
        cluster = _FakeCluster(avg_similarity=0.5)
        assert bridge.map_cluster_to_l3(cluster, min_similarity=0.7) is None

    def test_maps_when_thresholds_met(self, bridge: SomaticOntologyBridge) -> None:
        cluster = _FakeCluster()
        mapping = bridge.map_cluster_to_l3(cluster)
        assert mapping is not None
        assert mapping.target_layer == 3


# ── L4 escalation ────────────────────────────────────────────────────────


class TestProposeEscalationStrategy:

    def test_requires_high_confidence(self, bridge: SomaticOntologyBridge) -> None:
        precursor = _FakePrecursor(confidence=0.5)
        assert bridge.propose_escalation_strategy(precursor, min_confidence=0.8) is None

    def test_creates_candidate_when_confident(self, bridge: SomaticOntologyBridge) -> None:
        candidate = bridge.propose_escalation_strategy(_FakePrecursor())
        assert candidate is not None
        assert candidate.proposed_layer == 4

    def test_always_requires_governance(self, bridge: SomaticOntologyBridge) -> None:
        candidate = bridge.propose_escalation_strategy(_FakePrecursor())
        assert candidate is not None
        assert candidate.requires_governance is True


# ── Governance on all promotions ──────────────────────────────────────────


class TestGovernanceRequired:

    def test_l2_plus_promotions_require_governance(self, bridge: SomaticOntologyBridge) -> None:
        candidates = bridge.scan_promotion_candidates(
            episodes=[],
            fingerprints=[_FakeFingerprint(occurrence_count=5)],
            clusters=[_FakeCluster()],
            precursors=[_FakePrecursor()],
        )
        for c in candidates:
            if c.proposed_layer >= 2:
                assert c.requires_governance is True, (
                    f"L{c.proposed_layer} candidate must require governance"
                )


# ── scan_promotion_candidates ─────────────────────────────────────────────


class TestScanPromotionCandidates:

    def test_finds_valid_candidates(self, bridge: SomaticOntologyBridge) -> None:
        candidates = bridge.scan_promotion_candidates(
            episodes=[],
            fingerprints=[_FakeFingerprint(occurrence_count=4)],
            clusters=[_FakeCluster()],
            precursors=[_FakePrecursor()],
        )
        assert len(candidates) >= 2  # fingerprint + cluster at minimum

    def test_skips_below_threshold(self, bridge: SomaticOntologyBridge) -> None:
        candidates = bridge.scan_promotion_candidates(
            episodes=[],
            fingerprints=[_FakeFingerprint(occurrence_count=1)],
            clusters=[_FakeCluster(episode_ids=["e1"], avg_similarity=0.3)],
            precursors=[_FakePrecursor(confidence=0.2)],
        )
        assert len(candidates) == 0


# ── update_confidence ─────────────────────────────────────────────────────


class TestUpdateConfidence:

    def test_success_increases(self, bridge: SomaticOntologyBridge) -> None:
        fp = _FakeFingerprint(occurrence_count=3, fingerprint_id="uc-01")
        bridge.map_fingerprint_to_l2(fp)
        original = bridge.get_mappings_by_layer(2)[0].confidence
        assert original < 0.99  # starts below ceiling
        updated = bridge.update_confidence("uc-01", success=True)
        assert updated > original

    def test_failure_decreases(self, bridge: SomaticOntologyBridge) -> None:
        fp = _FakeFingerprint(occurrence_count=5, fingerprint_id="uc-02")
        bridge.map_fingerprint_to_l2(fp)
        original = bridge.get_mappings_by_layer(2)[0].confidence
        updated = bridge.update_confidence("uc-02", success=False)
        assert updated < original

    def test_confidence_has_floor(self, bridge: SomaticOntologyBridge) -> None:
        bridge.map_episode_to_l1(_FakeEpisode(episode_id="uc-03"))
        for _ in range(200):
            bridge.update_confidence("uc-03", success=False)
        final = bridge.get_mappings_by_layer(1)[0].confidence
        assert final >= 0.01

    def test_confidence_has_ceiling(self, bridge: SomaticOntologyBridge) -> None:
        bridge.map_episode_to_l1(_FakeEpisode(episode_id="uc-04"))
        for _ in range(200):
            bridge.update_confidence("uc-04", success=True)
        final = bridge.get_mappings_by_layer(1)[0].confidence
        assert final <= 0.99


# ── Persistence ───────────────────────────────────────────────────────────


class TestPersistence:

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        path = str(tmp_path / "rt.jsonl")
        b1 = SomaticOntologyBridge(mappings_path=path)
        b1.map_episode_to_l1(_FakeEpisode(episode_id="rt-01"))
        b1.map_fingerprint_to_l2(_FakeFingerprint(occurrence_count=5, fingerprint_id="rt-02"))
        b1.propose_escalation_strategy(_FakePrecursor(pattern_id="rt-03"))

        b2 = SomaticOntologyBridge(mappings_path=path)
        assert len(b2.get_mappings_by_layer(1)) == 1
        assert len(b2.get_mappings_by_layer(2)) == 1
        assert b2.get_mappings_by_layer(1)[0].source_id == "rt-01"

    def test_audit_report_not_empty(self, bridge: SomaticOntologyBridge) -> None:
        bridge.map_episode_to_l1(_FakeEpisode())
        report = bridge.to_audit_report()
        assert "Layer 1" in report
        assert "ep-001" in report
