"""Area 3: runtime calibrated activation and weighted salience."""

from attention.consolidation.attention_memory import AttentionMemory
from attention.core.attention_target import AttentionTarget
from attention.runtime.calibrated_attention_activation import CalibratedAttentionActivation
from attention.runtime.confidence_weighted_salience import ConfidenceWeightedSalience


def test_weighted_salience_never_amplifies() -> None:
    ws = ConfidenceWeightedSalience()
    r = ws.weight(0.6, 0.9)
    assert r.weighted <= 0.6


def test_calibrated_activation_includes_confidence(calibration_kernel) -> None:
    act = CalibratedAttentionActivation(kernel=calibration_kernel)
    mem = AttentionMemory(target_id="t1", domain="telemetry", salience_mean=0.7, salience_peak=0.8)
    result = act.activate_from_memory(mem, raw_confidence=0.75)
    assert "calibrated_confidence" in result


def test_submit_calibrated_target(calibration_kernel) -> None:
    act = CalibratedAttentionActivation(kernel=calibration_kernel)
    t = AttentionTarget(source_domain="telemetry", signal_type="cal", raw_value=0.65)
    result = act.submit_calibrated_target(t, raw_confidence=0.8)
    assert result.get("calibrated_confidence", 0) < 1.0
