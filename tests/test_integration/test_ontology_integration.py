"""Integration tests for v0.3.1 ontology cross-system integration.

Verifies that the ontology layer works correctly alongside existing modules
without conflicts, circular imports, or contract violations.
"""

from __future__ import annotations

import importlib
import sys
from datetime import datetime, timezone

import pytest


class TestOntologyModuleImports:
    """Verify ontology modules can be imported alongside existing modules."""

    def test_ontology_imports_alongside_skills(self):
        from memory.ontology import MemoryLayer, LAYER_REGISTRY
        from skills.core.skill_registry import SkillRegistry
        assert len(LAYER_REGISTRY) == 4
        assert SkillRegistry is not None

    def test_ontology_imports_alongside_attention(self):
        from memory.ontology import ConfidenceModel
        from attention.salience_engine import SalienceEngine
        assert ConfidenceModel is not None
        assert SalienceEngine is not None

    def test_ontology_imports_alongside_somatic_memory(self):
        from memory.ontology import EpisodicEntry
        from memory.somatic.sensor_episode_store import SomaticEpisodeStore
        assert EpisodicEntry is not None
        assert SomaticEpisodeStore is not None

    def test_ontology_imports_alongside_governance(self):
        from memory.ontology import PromotionEngine
        from governance.policy_engine import PolicyEngine
        assert PromotionEngine is not None
        assert PolicyEngine is not None

    def test_no_namespace_collisions(self):
        from memory.ontology.skill_schema import SkillMemoryEntry
        from skills.core.skill_schema import SkillSchema
        assert SkillMemoryEntry is not SkillSchema
        assert SkillMemoryEntry.__module__ == "memory.ontology.skill_schema"
        assert SkillSchema.__module__ == "skills.core.skill_schema"


class TestSomaticOntologyBridgeIntegration:
    """Test SomaticOntologyBridge with real SensorEpisode objects."""

    def test_bridge_accepts_sensor_episode(self, tmp_path, sample_sensor_episode):
        from memory.somatic.ontology_bridge import SomaticOntologyBridge

        mappings_file = str(tmp_path / "mappings.jsonl")
        bridge = SomaticOntologyBridge(mappings_path=mappings_file)
        mapping = bridge.map_episode_to_l1(sample_sensor_episode)

        assert mapping.source_id == sample_sensor_episode.episode_id
        assert mapping.target_layer == 1
        assert mapping.confidence == 1.0
        assert mapping.source_type == "episode"

    def test_bridge_mappings_persist(self, tmp_path, sample_sensor_episode):
        from memory.somatic.ontology_bridge import SomaticOntologyBridge

        mappings_file = str(tmp_path / "mappings.jsonl")
        bridge = SomaticOntologyBridge(mappings_path=mappings_file)
        bridge.map_episode_to_l1(sample_sensor_episode)

        bridge2 = SomaticOntologyBridge(mappings_path=mappings_file)
        assert len(bridge2.get_mappings_by_layer(1)) == 1


class TestConfidenceValidatorIntegration:
    """Test ConfidenceValidator integrates with PromotionEngine concepts."""

    def test_validator_blocks_self_certification(self):
        from governance.doctrine.confidence_validation import ConfidenceValidator

        validator = ConfidenceValidator()
        req = validator.request_verification(
            artifact_id="candidate-001",
            artifact_type="promotion_proposal",
            implementer_id="agent-alpha",
        )
        with pytest.raises(ValueError, match="Self-certification rejected"):
            validator.submit_verification(
                request_id=req.request_id,
                verifier_id="agent-alpha",
                confidence=0.9,
                approved=True,
            )

    def test_validator_allows_independent_verification(self):
        from governance.doctrine.confidence_validation import ConfidenceValidator

        validator = ConfidenceValidator()
        req = validator.request_verification(
            artifact_id="candidate-002",
            artifact_type="promotion_proposal",
            implementer_id="agent-alpha",
        )
        result = validator.submit_verification(
            request_id=req.request_id,
            verifier_id="agent-beta",
            confidence=0.85,
            approved=True,
        )
        assert result.approved is True

        allowed, reasons = validator.check_promotion_allowed("candidate-002", target_layer=2)
        assert allowed is True

    def test_validator_blocks_unverified_l2_promotion(self):
        from governance.doctrine.confidence_validation import ConfidenceValidator

        validator = ConfidenceValidator()
        allowed, reasons = validator.check_promotion_allowed("unknown-artifact", target_layer=2)
        assert allowed is False
        assert len(reasons) > 0


class TestDecayEngineIntegration:
    """Test DecayEngine can process entries from all 4 schema types."""

    def _make_entries(self):
        from memory.ontology import (
            EpisodicEntry, InstinctEntry, SkillMemoryEntry, StrategicEntry,
            DECAY_RULES, ConfidenceModel, DecayEngine,
        )

        now = datetime.now(timezone.utc)
        entries = [
            EpisodicEntry(
                entry_id="ep-001", timestamp=now, source="test",
                content="test episode", tags=["test"], signal_types=["cpu"],
                environmental_context={}, confidence=0.8,
            ),
            InstinctEntry(
                entry_id="inst-001", timestamp=now,
                source_episodes=["ep-001"], observation="CPU spikes precede OOM",
                trigger_conditions=["cpu > 90%"], confidence=0.75,
                occurrence_count=5,
            ),
            SkillMemoryEntry(
                entry_id="skill-001", timestamp=now,
                source_instincts=["inst-001"], skill_name="preemptive_gc",
                description="Run GC before OOM", workflow_steps=["detect", "gc"],
                confidence=0.85, execution_count=10,
            ),
            StrategicEntry(
                entry_id="strat-001", timestamp=now,
                source_skills=["skill-001"], heuristic="Always preempt OOM",
                applicability_scope="all_services", confidence=0.92,
                governance_approval_id="gov-001",
            ),
        ]
        model = ConfidenceModel()
        engine = DecayEngine(rules=DECAY_RULES, confidence_model=model)
        return entries, engine, now

    def test_decay_engine_processes_all_layers(self):
        from datetime import timedelta
        entries, engine, now = self._make_entries()
        future = now + timedelta(days=10)
        reports = engine.apply_time_decay(entries, future)
        assert len(reports) == 4
        for report in reports:
            assert report.previous_confidence >= report.new_confidence

    def test_decay_reports_are_human_readable(self):
        from datetime import timedelta
        entries, engine, now = self._make_entries()
        future = now + timedelta(days=10)
        reports = engine.apply_time_decay(entries, future)
        text = engine.generate_report(reports)
        assert "Decay Report" in text
        assert "entries affected" in text


class TestPromotionEngineIntegration:
    """Test PromotionEngine handles candidates from SomaticOntologyBridge."""

    def test_promotion_engine_with_bridge_candidates(self, tmp_path):
        from memory.ontology import (
            PromotionEngine, ConfidenceModel, PROMOTION_RULES, MemoryLayer,
            EpisodicEntry,
        )

        model = ConfidenceModel()
        engine = PromotionEngine(rules=PROMOTION_RULES, confidence_model=model)

        now = datetime.now(timezone.utc)
        entries = [
            EpisodicEntry(
                entry_id=f"ep-{i:03d}", timestamp=now, source="somatic_bridge",
                content=f"episode {i}", tags=["somatic"], signal_types=["cpu"],
                environmental_context={}, confidence=0.8, access_count=5,
            )
            for i in range(5)
        ]

        candidates = engine.scan_candidates(entries, MemoryLayer.L1_EPISODIC)
        assert len(candidates) == 5
        for c in candidates:
            assert c.source_layer == MemoryLayer.L1_EPISODIC
            assert c.target_layer == MemoryLayer.L2_INSTINCT


class TestBootOntology:
    """Test boot_ontology() succeeds."""

    def test_boot_ontology_returns_all_ok(self):
        from integration.v031_boot import boot_ontology
        results = boot_ontology()
        assert results["_summary"]["all_passed"] is True
        assert results["_summary"]["ok"] == results["_summary"]["total"]

    def test_boot_ontology_individual_checks(self):
        from integration.v031_boot import boot_ontology
        results = boot_ontology()
        assert results["layer_definitions"]["status"] == "ok"
        assert results["promotion_rules"]["status"] == "ok"
        assert results["decay_rules"]["status"] == "ok"
        assert results["confidence_model"]["status"] == "ok"
        assert results["somatic_bridge"]["status"] == "ok"
        assert results["governance_doctrine"]["status"] == "ok"
        assert results["schemas"]["status"] == "ok"


class TestVerifyOntology:
    """Test verify_ontology() passes all checks."""

    def test_verify_ontology_all_pass(self):
        from integration.v031_boot import verify_ontology
        checks = verify_ontology()
        for name, (passed, detail) in checks.items():
            assert passed, f"Check {name!r} failed: {detail}"

    def test_verify_ontology_has_expected_checks(self):
        from integration.v031_boot import verify_ontology
        checks = verify_ontology()
        expected = {
            "modules_importable",
            "layer_registry_count",
            "promotion_rules_count",
            "decay_rules_count",
            "somatic_bridge",
            "governance_doctrine",
            "backward_compat_somatic",
            "backward_compat_skills",
            "backward_compat_attention",
        }
        assert set(checks.keys()) == expected


class TestBackwardCompatibility:
    """Test existing v0.4 imports still work after ontology addition."""

    def test_v04_skills_still_importable(self):
        from skills.core.skill_registry import SkillRegistry
        from skills.core.skill_router import SkillRouter
        from skills.core.skill_validator import SkillValidator
        assert all(cls is not None for cls in [SkillRegistry, SkillRouter, SkillValidator])

    def test_v04_attention_still_importable(self):
        from attention.salience_engine import SalienceEngine
        from attention.novelty_detector import NoveltyDetector
        from attention.weak_signal_detector import WeakSignalDetector
        assert all(cls is not None for cls in [SalienceEngine, NoveltyDetector, WeakSignalDetector])

    def test_v04_somatic_memory_still_importable(self):
        from memory.somatic.sensor_episode_store import SomaticEpisodeStore
        from memory.somatic.environmental_signature import EnvironmentalSignature
        from memory.somatic.pattern_similarity import PatternSimilarity
        assert all(cls is not None for cls in [SomaticEpisodeStore, EnvironmentalSignature, PatternSimilarity])

    def test_v04_skillify_still_importable(self):
        from agents.skillify.workflow_observer import WorkflowObserver
        from agents.skillify.pattern_miner import SkillifyPatternMiner
        assert all(cls is not None for cls in [WorkflowObserver, SkillifyPatternMiner])


class TestNoCircularImports:
    """Verify no circular imports between ontology and existing modules."""

    ONTOLOGY_MODULES = [
        "memory.ontology",
        "memory.ontology.layer_definition",
        "memory.ontology.episodic_schema",
        "memory.ontology.instinct_schema",
        "memory.ontology.skill_schema",
        "memory.ontology.strategic_schema",
        "memory.ontology.promotion_rules",
        "memory.ontology.decay_rules",
        "memory.ontology.confidence_model",
        "memory.ontology.promotion_engine",
        "memory.ontology.decay_engine",
    ]

    EXISTING_MODULES = [
        "memory.somatic.sensor_episode_store",
        "memory.somatic.ontology_bridge",
        "governance.doctrine.confidence_validation",
        "skills.core.skill_registry",
        "attention.salience_engine",
    ]

    def test_ontology_modules_import_cleanly(self):
        for mod_name in self.ONTOLOGY_MODULES:
            mod = importlib.import_module(mod_name)
            assert mod is not None, f"Failed to import {mod_name}"

    def test_existing_modules_import_after_ontology(self):
        for mod_name in self.ONTOLOGY_MODULES:
            importlib.import_module(mod_name)
        for mod_name in self.EXISTING_MODULES:
            mod = importlib.import_module(mod_name)
            assert mod is not None, f"Failed to import {mod_name} after ontology"

    def test_no_circular_dependency_detection(self):
        for mod_name in self.ONTOLOGY_MODULES:
            if mod_name in sys.modules:
                del sys.modules[mod_name]

        for mod_name in self.ONTOLOGY_MODULES:
            try:
                importlib.import_module(mod_name)
            except ImportError as exc:
                if "circular" in str(exc).lower():
                    pytest.fail(f"Circular import detected in {mod_name}: {exc}")
                raise
