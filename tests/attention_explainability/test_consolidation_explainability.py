"""Unit tests for the consolidation-explainability modules (v052 contract)."""

from __future__ import annotations

from attention.consolidation.attention_memory import AttentionMemory
from attention.core.precursor_signal import PrecursorSignal
from attention.explainability.consolidation_explainer import ConsolidationExplainer
from attention.explainability.noise_suppression_explainer import NoiseSuppressionExplainer
from attention.explainability.precursor_reinforcement_report import PrecursorReinforcementReport


def test_consolidation_explainer_rationale() -> None:
    mem = AttentionMemory(target_id="t1", domain="telemetry", salience_peak=0.8, trace_count=3)
    exp = ConsolidationExplainer().explain_memory(mem)
    assert "rationale" in exp
    assert exp["strong_salience"] is True
    assert exp["well_supported"] is True
    assert exp["opaque"] is False


def test_consolidation_explainer_weak() -> None:
    mem = AttentionMemory(target_id="t2", domain="telemetry", salience_peak=0.1, trace_count=1)
    exp = ConsolidationExplainer().explain_memory(mem)
    assert exp["strong_salience"] is False
    assert exp["well_supported"] is False
    assert "rationale" in exp


def test_precursor_reinforcement_bounded() -> None:
    p = PrecursorSignal(pattern_id="pat", strength=0.6)
    rep = PrecursorReinforcementReport().for_precursor(p)
    assert rep["reinforced_salience"] <= 1.0
    assert rep["reinforced_salience"] <= rep["ceiling"]


def test_precursor_reinforcement_high_strength_capped() -> None:
    p = PrecursorSignal(pattern_id="pat", strength=1.0)
    rep = PrecursorReinforcementReport().for_precursor(p, current_salience=0.9, hit_count=100)
    assert rep["reinforced_salience"] <= rep["ceiling"]


def test_noise_explainer_keeps_high_value() -> None:
    exp = NoiseSuppressionExplainer().explain("telemetry", "ping", 0.05)
    assert "is_noise" in exp
    assert exp["opaque"] is False


def test_noise_explainer_suppresses_repetitive_low() -> None:
    explainer = NoiseSuppressionExplainer()
    last = None
    for _ in range(4):
        last = explainer.explain("telemetry", "ping", 0.05)
    assert last is not None
    assert last["is_noise"] is True
    assert last["reason"] == "repetitive_low_salience"


def test_noise_explainer_high_value_not_noise() -> None:
    exp = NoiseSuppressionExplainer().explain("telemetry", "spike", 0.9)
    assert exp["is_noise"] is False
    assert exp["reason"] == "above_salience_ceiling"
