"""Area 7: observability v053 metrics."""

from attention.core.attention_target import AttentionTarget
from observability.v053.forecast_metrics import collect_from_forecaster
from observability.v053.forecast_pressure import collect_forecast_pressure_metrics
from observability.v053.salience_projection_metrics import collect_salience_projection_metrics


def test_forecast_metrics(forecaster) -> None:
    t = AttentionTarget(source_domain="telemetry", signal_type="m", raw_value=0.5)
    forecaster.ingest(t)
    m = collect_from_forecaster(forecaster, t.target_id)
    assert m.projection_count > 0


def test_pressure_metrics(forecaster) -> None:
    t = AttentionTarget(source_domain="telemetry", signal_type="p", raw_value=0.4)
    m = collect_forecast_pressure_metrics(forecaster.pressure_forecast, t.target_id)
    assert 0.0 <= m.projected <= 1.0


def test_projection_metrics(forecaster) -> None:
    t = AttentionTarget(source_domain="telemetry", signal_type="sp", raw_value=0.45)
    forecaster.ingest(t)
    m = collect_salience_projection_metrics(forecaster.projection, t.target_id)
    assert m.step_count >= 0
