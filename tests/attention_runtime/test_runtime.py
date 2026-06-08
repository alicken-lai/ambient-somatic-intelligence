"""Unit tests for the attention.runtime / governance / explainability-runtime layer."""

from __future__ import annotations

from datetime import datetime, timezone

from attention.core.attention_target import AttentionTarget
from attention.core.precursor_signal import PrecursorSignal
from attention.core.salience import SalienceVector
from attention.governance.escalation_salience import escalation_boost
from attention.governance.guardian_attention_bridge import GuardianAttentionBridge
from attention.explainability.runtime_attention_explainer import RuntimeAttentionExplainer
from attention.explainability.runtime_salience_breakdown import runtime_breakdown_summary
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.attention_pressure_controller import AttentionPressureController
from attention.runtime.overload_recovery import OverloadRecovery
from attention.runtime.precursor_memory_bridge import PrecursorMemoryBridge
from attention.runtime.runtime_attention_budget import RuntimeAttentionBudget
from attention.runtime.runtime_memory_activation import RuntimeMemoryActivation
from attention.runtime.telemetry_attention_adapter import TelemetryAttentionAdapter
from attention.runtime.telemetry_attention_signal import telemetry_to_target
from telemetry.core.telemetry_schema import TelemetryRecord


def _kernel() -> AttentionKernel:
    return AttentionKernel(max_focus=5, max_queue=20)


def _record(i: int = 0) -> TelemetryRecord:
    return TelemetryRecord(
        source="test",
        timestamp=f"2026-05-19T00:00:0{i}+00:00",
        category="attention",
        payload={"salience": 0.7, "signal_type": f"sig-{i}"},
        confidence=1.0,
    )


# --- telemetry ---------------------------------------------------------------

def test_telemetry_to_target_domain() -> None:
    target = telemetry_to_target(_record())
    assert target.source_domain in ("task", "external", "somatic", "governance", "memory")
    assert target.raw_value == 0.7


def test_adapter_ingest_and_duplicate() -> None:
    adapter = TelemetryAttentionAdapter(_kernel())
    rec = _record()
    first = adapter.ingest(rec)
    assert first["accepted"] is True
    second = adapter.ingest(rec)
    assert second["accepted"] is False
    assert second["reason"] == "duplicate_submission"


def test_category_domain_mapping() -> None:
    gov = telemetry_to_target(TelemetryRecord(category="governance", payload={"salience": 0.4}))
    assert gov.source_domain == "governance"
    mem = telemetry_to_target(TelemetryRecord(category="episodic", payload={"salience": 0.4}))
    assert mem.source_domain == "memory"


# --- pressure / budget / recovery -------------------------------------------

def test_pressure_evaluate() -> None:
    ctrl = AttentionPressureController(_kernel())
    d = ctrl.evaluate()
    assert d.pressure.composite >= 0.0
    assert d.action in ("idle", "steady", "throttle")


def test_budget_consume_and_exhaust() -> None:
    budget = RuntimeAttentionBudget(_kernel(), total=0.1)
    assert budget.try_allocate("somatic", 0.05) is True
    assert budget.try_allocate("somatic", 0.05) is True
    assert budget.try_allocate("somatic", 0.05) is False


def test_overload_recovery_step() -> None:
    kernel = _kernel()
    kernel.state.fatigue_level = 0.5
    out = OverloadRecovery(kernel).step()
    assert "recovery" in out
    assert kernel.state.fatigue_level < 0.5


# --- memory activation -------------------------------------------------------

def test_memory_activation_cap() -> None:
    act = RuntimeMemoryActivation(_kernel(), max_activations=2)
    t = AttentionTarget("memory", "recall", 0.6, metadata={"tags": ["a"], "memory_relevance": 0.5})
    act.activate(t, ["a"])
    act.activate(t, ["a"])
    third = act.activate(t, ["a"])
    assert third["accepted"] is False
    assert third["reason"] == "activation_cap_reached"


def test_precursor_bridge() -> None:
    bridge = PrecursorMemoryBridge(RuntimeMemoryActivation(_kernel()))
    p = PrecursorSignal(pattern_id="pat-1", strength=0.6, domain="somatic", metadata={"tags": ["alert"]})
    r = bridge.from_precursor(p, recent_tags=["alert"])
    assert r["accepted"] is True
    assert "activation_level" in r


# --- governance --------------------------------------------------------------

def test_escalation_boost_ordering() -> None:
    assert escalation_boost("BLOCK") > escalation_boost("REVIEW_REQUIRED")
    assert escalation_boost("REVIEW_REQUIRED") > escalation_boost("ALLOW")
    assert escalation_boost("ALLOW") == 0.0


def test_guardian_bridge_submits() -> None:
    bridge = GuardianAttentionBridge(_kernel())
    r = bridge.from_guardian_result("git push", "REVIEW_REQUIRED", matched=["git"])
    assert r["accepted"] is True
    assert r["risk"] == "REVIEW_REQUIRED"


# --- runtime explainability --------------------------------------------------

def test_runtime_explainer_not_opaque() -> None:
    kernel = _kernel()
    expl = RuntimeAttentionExplainer(kernel)
    target = AttentionTarget("somatic", "cpu_spike", 0.85, metadata={"urgency": 0.9})
    out = expl.explain_target(target)
    assert out["total"] >= 0.0
    assert out["runtime_summary"]["opaque"] is False


def test_breakdown_summary() -> None:
    vec = SalienceVector("t1", {"urgency": 0.8, "novelty": 0.3})
    s = runtime_breakdown_summary(vec)
    assert s["factor_count"] >= 1
    assert s["opaque"] is False
