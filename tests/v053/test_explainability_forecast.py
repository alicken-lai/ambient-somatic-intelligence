"""Area 6: forecast explainability."""

from attention.core.attention_target import AttentionTarget
from attention.explainability.forecast_explainer import ForecastExplainer
from attention.explainability.precursor_chain_explainer import PrecursorChainExplainer


def test_forecast_explainer(forecaster) -> None:
    t = AttentionTarget(source_domain="telemetry", signal_type="ex", raw_value=0.5)
    forecaster.ingest(t)
    result = forecaster.forecast(t.target_id)
    exp = ForecastExplainer().explain(result)
    assert "probabilistic" in exp["summary"].lower()
    assert exp["disclaimer"] == result.disclaimer


def test_precursor_chain_explainer() -> None:
    exp = PrecursorChainExplainer().explain_chain([])
    assert exp["chain_length"] == 0
