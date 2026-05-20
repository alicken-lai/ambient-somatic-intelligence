"""Area 7: observability v064 metrics."""

from observability.v064.attention_pathology_metrics import (
    collect_attention_pathology_metrics,
)
from observability.v064.calibration_reflection_metrics import (
    collect_calibration_reflection_metrics,
)
from observability.v064.cognition_quality_metrics import collect_cognition_quality_metrics
from observability.v064.degradation_metrics import collect_degradation_metrics
from observability.v064.reflection_boundary_metrics import (
    collect_reflection_boundary_metrics,
)


def test_all_metrics_collect() -> None:
    assert collect_cognition_quality_metrics().quality_rate >= 0.5
    assert collect_degradation_metrics().containment_rate >= 0.5
    assert collect_attention_pathology_metrics().containment_rate >= 0.5
    assert collect_reflection_boundary_metrics().compliance_rate >= 0.5
    assert collect_calibration_reflection_metrics().bounded_rate >= 0.5
