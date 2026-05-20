"""Area 6: observability v054 metrics."""

from attention.calibration.confidence_cap import ConfidenceCap
from attention.calibration.false_positive_tracker import FalsePositiveTracker
from observability.v054.calibration_metrics import collect_calibration_metrics
from observability.v054.confidence_cap_metrics import collect_confidence_cap_metrics
from observability.v054.false_positive_metrics import collect_false_positive_metrics
from observability.v054.humility_metrics import collect_humility_metrics
from attention.calibration.forecast_humility import ForecastHumility


def test_calibration_metrics_no_violations() -> None:
    m = collect_calibration_metrics([0.9, 0.85, 0.92])
    assert m.certainty_violations == 0


def test_cap_metrics() -> None:
    m = collect_confidence_cap_metrics(ConfidenceCap(), [1.0, 0.5])
    assert m.violations >= 1


def test_fp_and_humility_metrics() -> None:
    fp = collect_false_positive_metrics(FalsePositiveTracker())
    hum = collect_humility_metrics(ForecastHumility(), [0.9, 0.5])
    assert fp.record_count == 0
    assert hum.mean_humility_factor <= 1.0
