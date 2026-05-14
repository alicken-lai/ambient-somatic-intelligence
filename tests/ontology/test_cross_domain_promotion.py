"""Phase 0D — Cross-Domain Generalization Stress Test.

Simulates thermal drift across 3 domains and verifies cross-domain
instinct clustering, L3 skill formation, and L4 strategic proposal.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.skill_schema import SkillMemoryEntry
from memory.ontology.strategic_schema import StrategicEntry
from memory.ontology.promotion_rules import PROMOTION_RULES, check_promotion_eligibility
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.promotion_engine import PromotionEngine, PromotionCandidate
from memory.somatic.anomaly_fingerprint import AnomalyFingerprint


DOMAIN_A_SIGNALS = ["rack_thermal", "fan_mismatch"]
DOMAIN_B_SIGNALS = ["hvac_thermal", "duct_blockage"]
DOMAIN_C_SIGNALS = ["coolant_thermal", "radiator_blockage"]


def _make_domain_instinct(
    domain: str,
    signal_types: list[str],
    confidence: float = 0.85,
    occurrence_count: int = 6,
    contexts: list[str] | None = None,
) -> InstinctEntry:
    return InstinctEntry(
        entry_id=f"inst-{domain}-{uuid.uuid4().hex[:6]}",
        timestamp=datetime.now(timezone.utc),
        source_episodes=[f"ep-{domain}-{i}" for i in range(5)],
        observation=f"Thermal pattern in {domain} domain correlates with degradation",
        trigger_conditions=signal_types,
        confidence=confidence,
        contextual_applicability=contexts or [domain, "thermal_general"],
        occurrence_count=occurrence_count,
        success_count=int(occurrence_count * 0.8),
        failure_count=int(occurrence_count * 0.2),
        last_validated=datetime.now(timezone.utc),
    )


def _make_domain_episodic_entries(
    domain: str, signal_types: list[str], n: int = 10
) -> list[EpisodicEntry]:
    base_time = datetime(2025, 6, 1, tzinfo=timezone.utc)
    return [
        EpisodicEntry(
            entry_id=f"ep-{domain}-{i:04d}",
            timestamp=base_time + timedelta(hours=i),
            source=f"{domain}_sensor",
            content=f"{domain} thermal event #{i}",
            tags=[domain, "thermal"],
            signal_types=signal_types,
            environmental_context={"cpu_band": "heavy", "domain": domain},
            confidence=0.9,
            access_count=4,
        )
        for i in range(n)
    ]


class TestDomainACreatesInstinct:
    def test_domain_a_creates_instinct(self, promotion_engine):
        entries = _make_domain_episodic_entries("rack", DOMAIN_A_SIGNALS)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        for c in eligible:
            assert c.target_layer == MemoryLayer.L2_INSTINCT


class TestDomainBCreatesInstinct:
    def test_domain_b_creates_instinct(self, promotion_engine):
        entries = _make_domain_episodic_entries("hvac", DOMAIN_B_SIGNALS)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0


class TestDomainCCreatesInstinct:
    def test_domain_c_creates_instinct(self, promotion_engine):
        entries = _make_domain_episodic_entries("vehicle", DOMAIN_C_SIGNALS)
        candidates = promotion_engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0


class TestCrossDomainSimilarityDetected:
    def test_cross_domain_similarity_detected(self):
        """Instincts from different domains that share 'thermal' pattern should be similar."""
        fp_a = AnomalyFingerprint(
            fingerprint_id="fp-a",
            signal_pattern="FAN_MISMATCH+RACK_THERMAL",
            severity_band="high",
            env_context="env-heavy",
            temporal_pattern="sustained",
            occurrence_count=5,
        )
        fp_b = AnomalyFingerprint(
            fingerprint_id="fp-b",
            signal_pattern="DUCT_BLOCKAGE+HVAC_THERMAL",
            severity_band="high",
            env_context="env-heavy",
            temporal_pattern="sustained",
            occurrence_count=5,
        )
        fp_c = AnomalyFingerprint(
            fingerprint_id="fp-c",
            signal_pattern="COOLANT_THERMAL+RADIATOR_BLOCKAGE",
            severity_band="high",
            env_context="env-heavy",
            temporal_pattern="sustained",
            occurrence_count=5,
        )
        sim_ab = fp_a.match(fp_b)
        sim_bc = fp_b.match(fp_c)
        sim_ac = fp_a.match(fp_c)
        assert sim_ab > 0.0
        assert sim_bc > 0.0
        assert sim_ac > 0.0


class TestCrossDomainPromotionToL3:
    def test_cross_domain_promotion_to_l3(self, promotion_engine):
        """Clustered instincts from multiple contexts become skill candidates."""
        instincts = [
            _make_domain_instinct("rack", DOMAIN_A_SIGNALS, contexts=["rack", "thermal_general"]),
            _make_domain_instinct("hvac", DOMAIN_B_SIGNALS, contexts=["hvac", "thermal_general"]),
            _make_domain_instinct("vehicle", DOMAIN_C_SIGNALS, contexts=["vehicle", "thermal_general"]),
        ]
        candidates = promotion_engine.scan_candidates(instincts, MemoryLayer.L2_INSTINCT)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        for c in eligible:
            assert c.target_layer == MemoryLayer.L3_SKILL


class TestL3ToL4StrategicCandidate:
    def test_l3_to_l4_strategic_candidate(self, promotion_engine):
        """Cross-validated skill becomes strategic proposal."""
        skill = SkillMemoryEntry(
            entry_id="skill-cross-thermal",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-rack-001", "inst-hvac-001", "inst-vehicle-001"],
            skill_name="cross_domain_thermal_detection",
            description="Detect thermal drift across any domain",
            workflow_steps=["collect", "analyze", "alert"],
            confidence=0.92,
            execution_count=12,
            success_count=11,
            failure_count=1,
            contexts_validated=["rack", "hvac", "vehicle"],
        )
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        for c in eligible:
            assert c.target_layer == MemoryLayer.L4_STRATEGIC


class TestStrategicProposalRequiresGovernance:
    def test_strategic_proposal_requires_governance(self, promotion_engine):
        """L3→L4 promotion must fail without governance_decision_id."""
        skill = SkillMemoryEntry(
            entry_id="skill-gov-test",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-001"],
            skill_name="test_skill",
            description="test",
            workflow_steps=["step1"],
            confidence=0.95,
            execution_count=15,
            success_count=14,
            failure_count=1,
            contexts_validated=["ctx_a", "ctx_b"],
        )
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])
        result = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="",
        )
        assert not result.approved
        assert "Governance" in result.reason


class TestStrategicProposalRequiresVerifier:
    def test_strategic_proposal_requires_verifier(self, promotion_engine):
        """L3→L4 promotion must fail without verifier_id."""
        skill = SkillMemoryEntry(
            entry_id="skill-verifier-test",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-001"],
            skill_name="test_skill",
            description="test",
            workflow_steps=["step1"],
            confidence=0.95,
            execution_count=15,
            success_count=14,
            failure_count=1,
            contexts_validated=["ctx_a", "ctx_b"],
        )
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        eligible = [c for c in candidates if c.eligible]
        assert len(eligible) > 0
        promotion_engine.propose_promotion(eligible[0])
        result = promotion_engine.approve_promotion(
            eligible[0].candidate_id,
            governance_decision_id="gov-test-001",
            verifier_id=None,
        )
        assert not result.approved
        assert "verifier" in result.reason.lower()


class TestSimilarityMatrixGenerated:
    def test_similarity_matrix_generated(self):
        """Verify that pairwise similarity scores form a coherent matrix."""
        fingerprints = [
            AnomalyFingerprint(
                fingerprint_id=f"fp-{i}",
                signal_pattern=pattern,
                severity_band="high",
                env_context="env-heavy",
                temporal_pattern="sustained",
                occurrence_count=5,
            )
            for i, pattern in enumerate([
                "FAN_MISMATCH+RACK_THERMAL",
                "DUCT_BLOCKAGE+HVAC_THERMAL",
                "COOLANT_THERMAL+RADIATOR_BLOCKAGE",
            ])
        ]
        matrix = []
        for i, fp_a in enumerate(fingerprints):
            row = []
            for j, fp_b in enumerate(fingerprints):
                if i == j:
                    row.append(1.0)
                else:
                    row.append(fp_a.match(fp_b))
            matrix.append(row)

        for i in range(3):
            assert matrix[i][i] == 1.0
        for i in range(3):
            for j in range(3):
                assert 0.0 <= matrix[i][j] <= 1.0


class TestStrategicCandidateLogsEvidence:
    def test_strategic_candidate_logs_evidence(self, promotion_engine):
        """Promotion candidates must include evidence dict with occurrence_count."""
        skill = SkillMemoryEntry(
            entry_id="skill-evidence-test",
            timestamp=datetime.now(timezone.utc),
            source_instincts=["inst-001"],
            skill_name="evidence_skill",
            description="test",
            workflow_steps=["step1"],
            confidence=0.95,
            execution_count=12,
            success_count=11,
            failure_count=1,
            contexts_validated=["ctx_a", "ctx_b"],
        )
        candidates = promotion_engine.scan_candidates([skill], MemoryLayer.L3_SKILL)
        assert len(candidates) > 0
        c = candidates[0]
        assert "confidence" in c.evidence
        assert "occurrence_count" in c.evidence
        assert "success_rate" in c.evidence
