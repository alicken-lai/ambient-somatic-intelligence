"""Shared fixtures for ontology stress tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from memory.ontology.layer_definition import MemoryLayer, LAYER_REGISTRY
from memory.ontology.episodic_schema import EpisodicEntry
from memory.ontology.instinct_schema import InstinctEntry
from memory.ontology.skill_schema import SkillMemoryEntry
from memory.ontology.strategic_schema import StrategicEntry
from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.promotion_engine import PromotionEngine
from memory.ontology.promotion_rules import PROMOTION_RULES
from memory.ontology.decay_engine import DecayEngine
from memory.ontology.decay_rules import DECAY_RULES
from memory.somatic.sensor_episode_store import SensorEpisode
from memory.somatic.anomaly_fingerprint import AnomalyFingerprint
from memory.somatic.environmental_signature import EnvironmentalSignature


@pytest.fixture
def sandbox_dir(tmp_path):
    """Isolated sandbox directory — never touches production paths."""
    return tmp_path


@pytest.fixture
def confidence_model():
    """Fresh ConfidenceModel instance for each test."""
    return ConfidenceModel()


@pytest.fixture
def promotion_engine(confidence_model):
    """Fresh PromotionEngine with standard rules."""
    return PromotionEngine(rules=PROMOTION_RULES, confidence_model=confidence_model)


@pytest.fixture
def decay_engine(confidence_model):
    """Fresh DecayEngine with standard rules."""
    return DecayEngine(rules=DECAY_RULES, confidence_model=confidence_model)


@pytest.fixture
def synthetic_episode_generator():
    """Factory that generates N SensorEpisode objects with configurable parameters."""

    def _generate(
        n: int = 10,
        signal_types: list[str] | None = None,
        severity_range: tuple[float, float] = (0.5, 0.9),
        env_signature: dict[str, Any] | None = None,
        base_time: datetime | None = None,
        duration_ms: float = 1000.0,
    ) -> list[SensorEpisode]:
        signal_types = signal_types or ["thermal_drift"]
        env_signature = env_signature or {
            "cpu_band": "heavy",
            "memory_band": "moderate",
            "disk_band": "idle",
            "load_band": "moderate",
            "process_band": "normal",
            "composite_vector": [0.7, 0.5, 0.3, 0.4, 0.3],
        }
        base_time = base_time or datetime.now(timezone.utc)

        episodes = []
        for i in range(n):
            severity = severity_range[0] + (severity_range[1] - severity_range[0]) * (i / max(n - 1, 1))
            ep = SensorEpisode(
                episode_id=f"ep-synth-{uuid.uuid4().hex[:8]}",
                timestamp=base_time + timedelta(minutes=i * 5),
                duration_ms=duration_ms,
                source_signals=[
                    {"type": st, "value": severity, "urgency": 3}
                    for st in signal_types
                ],
                environmental_signature=dict(env_signature),
                anomaly_score=severity * 0.8,
                attention_score=severity * 0.6,
                severity_peak=severity,
                signal_types=list(signal_types),
                fingerprint=f"fp-{'+'.join(sorted(signal_types))}",
            )
            episodes.append(ep)
        return episodes

    return _generate


@pytest.fixture
def synthetic_fingerprint_generator():
    """Factory that generates AnomalyFingerprint objects."""

    def _generate(
        n: int = 5,
        signal_pattern: str = "THERMAL_DRIFT+FAN_MISMATCH",
        severity_band: str = "high",
        occurrence_count: int = 5,
    ) -> list[AnomalyFingerprint]:
        fingerprints = []
        for i in range(n):
            fp = AnomalyFingerprint(
                fingerprint_id=f"fp-{uuid.uuid4().hex[:12]}",
                signal_pattern=signal_pattern,
                severity_band=severity_band,
                env_context=f"env-context-{i:04d}",
                temporal_pattern="sustained",
                occurrence_count=occurrence_count,
                first_seen=datetime.now(timezone.utc) - timedelta(days=10),
                last_seen=datetime.now(timezone.utc),
            )
            fingerprints.append(fp)
        return fingerprints

    return _generate


@pytest.fixture
def synthetic_env_signature():
    """Factory that generates EnvironmentalSignature objects."""

    def _generate(
        cpu_band: str = "heavy",
        memory_band: str = "moderate",
        disk_band: str = "idle",
        load_band: str = "moderate",
        process_band: str = "normal",
    ) -> EnvironmentalSignature:
        band_to_val = {
            "idle": 0.1, "light": 0.3, "moderate": 0.5,
            "heavy": 0.7, "saturated": 0.9,
            "low": 0.2, "normal": 0.4, "high": 0.6, "excessive": 0.9,
        }
        return EnvironmentalSignature(
            cpu_band=cpu_band,
            memory_band=memory_band,
            disk_band=disk_band,
            load_band=load_band,
            process_band=process_band,
            composite_vector=[
                band_to_val.get(cpu_band, 0.5),
                band_to_val.get(memory_band, 0.5),
                band_to_val.get(disk_band, 0.5),
                band_to_val.get(load_band, 0.5),
                band_to_val.get(process_band, 0.5),
            ],
        )

    return _generate


@pytest.fixture
def make_episodic_entry():
    """Factory for EpisodicEntry instances with sensible defaults."""

    def _make(
        signal_types: list[str] | None = None,
        confidence: float = 0.8,
        access_count: int = 5,
        environmental_context: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        last_accessed: datetime | None = None,
    ) -> EpisodicEntry:
        return EpisodicEntry(
            entry_id=f"epi-{uuid.uuid4().hex[:8]}",
            timestamp=timestamp or datetime.now(timezone.utc),
            source="stress_test",
            content="Synthetic episodic entry for stress testing",
            tags=["stress_test", "synthetic"],
            signal_types=signal_types or ["thermal_drift"],
            environmental_context=environmental_context or {
                "cpu_band": "heavy",
                "memory_band": "moderate",
            },
            confidence=confidence,
            access_count=access_count,
            last_accessed=last_accessed,
        )

    return _make


@pytest.fixture
def make_instinct_entry():
    """Factory for InstinctEntry instances with sensible defaults."""

    def _make(
        observation: str = "Thermal drift correlates with component failure",
        confidence: float = 0.85,
        occurrence_count: int = 10,
        success_count: int = 8,
        failure_count: int = 2,
        contextual_applicability: list[str] | None = None,
        timestamp: datetime | None = None,
        last_validated: datetime | None = None,
        contradiction_count: int = 0,
    ) -> InstinctEntry:
        return InstinctEntry(
            entry_id=f"inst-{uuid.uuid4().hex[:8]}",
            timestamp=timestamp or datetime.now(timezone.utc),
            source_episodes=[f"ep-{uuid.uuid4().hex[:8]}" for _ in range(3)],
            observation=observation,
            trigger_conditions=["thermal_drift", "fan_mismatch"],
            confidence=confidence,
            contextual_applicability=contextual_applicability or ["rack_thermal"],
            occurrence_count=occurrence_count,
            success_count=success_count,
            failure_count=failure_count,
            last_validated=last_validated,
            contradiction_count=contradiction_count,
        )

    return _make


@pytest.fixture
def make_skill_entry():
    """Factory for SkillMemoryEntry instances with sensible defaults."""

    def _make(
        confidence: float = 0.85,
        execution_count: int = 15,
        success_count: int = 12,
        failure_count: int = 3,
        contexts_validated: list[str] | None = None,
        timestamp: datetime | None = None,
        last_executed: datetime | None = None,
    ) -> SkillMemoryEntry:
        return SkillMemoryEntry(
            entry_id=f"skill-{uuid.uuid4().hex[:8]}",
            timestamp=timestamp or datetime.now(timezone.utc),
            source_instincts=[f"inst-{uuid.uuid4().hex[:8]}" for _ in range(3)],
            skill_name="thermal_drift_detection",
            description="Detect and respond to thermal drift patterns",
            workflow_steps=["collect_signals", "analyze_pattern", "take_action"],
            confidence=confidence,
            execution_count=execution_count,
            success_count=success_count,
            failure_count=failure_count,
            contexts_validated=contexts_validated or ["rack_a", "rack_b"],
            last_executed=last_executed,
        )

    return _make


@pytest.fixture
def make_strategic_entry():
    """Factory for StrategicEntry instances with sensible defaults."""

    def _make(
        confidence: float = 0.92,
        validation_count: int = 20,
        cross_project_validations: list[str] | None = None,
        governance_approval_id: str = "gov-001",
        verifier_id: str = "verifier-independent-001",
        timestamp: datetime | None = None,
        last_applied: datetime | None = None,
    ) -> StrategicEntry:
        return StrategicEntry(
            entry_id=f"strat-{uuid.uuid4().hex[:8]}",
            timestamp=timestamp or datetime.now(timezone.utc),
            source_skills=[f"skill-{uuid.uuid4().hex[:8]}" for _ in range(2)],
            heuristic="Thermal drift above 0.7 severity always precedes failure within 24h",
            applicability_scope="all_thermal_systems",
            confidence=confidence,
            validation_count=validation_count,
            cross_project_validations=cross_project_validations or ["proj_a", "proj_b", "proj_c"],
            governance_approval_id=governance_approval_id,
            verifier_id=verifier_id,
            last_applied=last_applied,
        )

    return _make
