"""Area 6: consolidation explainability."""

from attention.consolidation.attention_memory import AttentionMemory
from attention.explainability.consolidation_explainer import ConsolidationExplainer
from attention.explainability.noise_suppression_explainer import NoiseSuppressionExplainer
from attention.explainability.precursor_reinforcement_report import PrecursorReinforcementReport
from attention.core.precursor_signal import PrecursorSignal


def test_consolidation_explainer() -> None:
    mem = AttentionMemory(target_id="t1", domain="telemetry", salience_peak=0.8, trace_count=3)
    exp = ConsolidationExplainer().explain_memory(mem)
    assert "rationale" in exp


def test_precursor_report() -> None:
    p = PrecursorSignal(pattern_id="pat", strength=0.6)
    rep = PrecursorReinforcementReport().for_precursor(p)
    assert rep["reinforced_salience"] <= 1.0


def test_noise_explainer() -> None:
    exp = NoiseSuppressionExplainer().explain("telemetry", "ping", 0.05)
    assert "is_noise" in exp
