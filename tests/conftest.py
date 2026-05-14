"""Shared fixtures for all Ambient OS v0.4 test suites."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from skills.core.skill_schema import (
    SkillContext,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillResult,
    SkillSchema,
)
from attention.attention_state import AttentionSignal
from memory.somatic.sensor_episode_store import SensorEpisode
from memory.somatic.environmental_signature import EnvironmentalSignature
from agents.skillify.workflow_observer import WorkflowEvent, WorkflowStep


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Isolated temporary directory for file I/O tests."""
    return tmp_path


@pytest.fixture
def sample_skill_schema() -> SkillSchema:
    """A minimal valid SkillSchema for reuse across tests."""

    def _execute(ctx: SkillContext) -> SkillResult:
        return SkillResult(
            success=True,
            outputs={"answer": "ok"},
            confidence=0.9,
        )

    return SkillSchema(
        name="test-skill",
        version="1.0.0",
        description="A test skill for unit tests",
        inputs=[
            SkillInput(
                name="task_description",
                type_hint="str",
                required=True,
                description="Task to execute",
            )
        ],
        outputs=[
            SkillOutput(
                name="answer",
                type_hint="str",
                description="The result",
            )
        ],
        execute=_execute,
        routing_conditions=["test", "unit"],
        memory_updates=["record_execution"],
        governance_level="ALLOW",
        observability_hooks=["log_execution"],
        metadata=SkillMetadata(tags=["testing", "unit"]),
    )


@pytest.fixture
def sample_attention_signal() -> AttentionSignal:
    """A valid AttentionSignal for reuse across tests."""
    return AttentionSignal(
        source_domain="somatic",
        signal_type="cpu_spike",
        raw_value=0.75,
        metadata={"sub_type": "sustained"},
    )


@pytest.fixture
def sample_sensor_episode() -> SensorEpisode:
    """A valid SensorEpisode for reuse across tests."""
    return SensorEpisode(
        episode_id="ep-test-0001",
        timestamp=datetime.now(timezone.utc),
        duration_ms=1500.0,
        source_signals=[
            {"type": "cpu_spike", "value": 0.8, "urgency": 3}
        ],
        environmental_signature={
            "cpu_band": "heavy",
            "memory_band": "moderate",
            "disk_band": "idle",
            "load_band": "moderate",
            "process_band": "normal",
            "composite_vector": [0.7, 0.5, 0.3, 0.4, 0.3],
        },
        anomaly_score=0.72,
        attention_score=0.65,
        severity_peak=0.8,
        signal_types=["cpu_spike"],
    )


@pytest.fixture
def sample_workflow_event() -> WorkflowEvent:
    """A valid WorkflowEvent for reuse across tests."""
    return WorkflowEvent.create(
        workflow_type="anomaly_detection",
        steps=[
            WorkflowStep(
                step_name="collect_signals",
                module="sensors",
                function="collect",
                duration_ms=120.0,
                success=True,
            ),
            WorkflowStep(
                step_name="evaluate_anomaly",
                module="somatic",
                function="evaluate",
                duration_ms=340.0,
                success=True,
            ),
        ],
        inputs={"description": "Check for CPU anomalies"},
        outputs={"anomaly_detected": True, "score": 0.78},
        success=True,
        duration_ms=460.0,
    )


@pytest.fixture
def sample_env_signature() -> EnvironmentalSignature:
    """A valid EnvironmentalSignature for reuse across tests."""
    return EnvironmentalSignature(
        cpu_band="moderate",
        memory_band="light",
        disk_band="idle",
        load_band="light",
        process_band="normal",
        composite_vector=[0.45, 0.35, 0.25, 0.2, 0.4],
    )
