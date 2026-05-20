"""Area 5: unified attention forecast."""

from attention.core.attention_target import AttentionTarget
from attention.forecasting.attention_forecast import AttentionForecast


def test_unified_forecast(forecaster: AttentionForecast) -> None:
    t = AttentionTarget(source_domain="telemetry", signal_type="fc", raw_value=0.55)
    forecaster.ingest(t)
    result = forecaster.forecast(t.target_id, "24h")
    assert result.disclaimer == "probabilistic_projection_not_prediction"
    assert result.trajectory is not None
    assert result.pressure is not None


def test_all_windows(forecaster: AttentionForecast) -> None:
    t = AttentionTarget(source_domain="somatic", signal_type="w", raw_value=0.4)
    forecaster.ingest(t)
    all_r = forecaster.forecast_all_windows(t.target_id)
    assert set(all_r.keys()) == {"6h", "24h", "7d", "30d"}
