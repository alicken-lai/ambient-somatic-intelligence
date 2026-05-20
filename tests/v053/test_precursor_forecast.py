"""Area 9: precursor forecast."""

from attention.core.precursor_signal import PrecursorSignal
from attention.forecasting.precursor_forecast import PrecursorForecast
from attention.consolidation.precursor_memory import PrecursorMemory
from observability.v053.precursor_forecast_metrics import collect_precursor_forecast_metrics


def test_precursor_forecast_match() -> None:
    mem = PrecursorMemory()
    sig = PrecursorSignal(pattern_id="pat-a", strength=0.7, domain="telemetry")
    mem.remember(sig)
    fc = PrecursorForecast(mem)
    pt = fc.forecast_from_signal(sig)
    assert pt is not None
    assert pt.likelihood > 0.0


def test_precursor_metrics() -> None:
    fc = PrecursorForecast()
    sig = PrecursorSignal(pattern_id="x", strength=0.5, domain="somatic")
    m = collect_precursor_forecast_metrics(fc, [sig])
    assert m.match_count >= 0
