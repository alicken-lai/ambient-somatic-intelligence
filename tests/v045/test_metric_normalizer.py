"""Consistent pressure → dimension mapping."""

from kernel.entropy.entropy_metric import EntropyMetric, MetricKind, MetricSnapshot
from kernel.entropy.entropy_controller import EntropyReport, EntropyClassification
from observability.v04.metric_normalizer import (
    dimension_from_pressure,
    pressure_max,
)


def _report(*metrics: EntropyMetric) -> EntropyReport:
    return EntropyReport(
        score=0.1,
        classification=EntropyClassification.STABLE,
        snapshot=MetricSnapshot(metrics=metrics, captured_at=""),
    )


def test_pressure_max_not_mean() -> None:
    ent = _report(
        EntropyMetric("patch_leakage", MetricKind.PATCH, 0.0),
        EntropyMetric("patch_churn", MetricKind.PATCH, 0.9),
    )
    assert pressure_max(ent, "patch_leakage", "patch_churn") == 0.9
    assert pressure_max(ent, "patch_leakage") == 0.0


def test_dimension_from_pressure_clamps() -> None:
    assert dimension_from_pressure(0.0) == 1.0
    assert dimension_from_pressure(1.0) == 0.0
    assert dimension_from_pressure(1.5) == 0.0
