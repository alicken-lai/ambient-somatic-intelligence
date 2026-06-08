"""Unit tests for the attention.somatic subpackage (v051-v054 contracts).

These verify the somatic modules directly, independent of the v051/v053/v054
version directories whose conftests are gated on the not-yet-rebuilt
runtime/forecasting layers.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from attention.attention_state import AttentionSignal
from attention.calibration.confidence_cap import (
    ABSOLUTE_MAX_CONFIDENCE,
    ConfidenceCap,
    apply_confidence_cap,
)
from attention.core.precursor_signal import PrecursorSignal
from attention.kernel.attention_kernel import AttentionKernel
from attention.somatic.environmental_resonance import EnvironmentalResonance
from attention.somatic.environmental_risk_projection import (
    RISK_CEILING,
    EnvironmentalRiskProjector,
)
from attention.somatic.environmental_uncertainty import EnvironmentalUncertainty
from attention.somatic.precursor_reliability import PrecursorReliability
from attention.somatic.precursor_resonance_forecast import PrecursorResonanceForecaster
from attention.somatic.runtime_somatic_attention import RuntimeSomaticAttention
from attention.somatic.somatic_confidence import SomaticConfidenceCalibrator
from attention.somatic.somatic_episode import SomaticEpisode
from attention.somatic.somatic_episode_store import SomaticEpisodeStore
from attention.somatic.somatic_forecast import SomaticForecast
from attention.somatic.somatic_runtime_bridge import SomaticRuntimeBridge


# --- confidence_cap primitive ------------------------------------------------

def test_absolute_max_below_certainty() -> None:
    assert ABSOLUTE_MAX_CONFIDENCE < 1.0


def test_apply_confidence_cap_never_certain() -> None:
    assert apply_confidence_cap(1.0) <= ABSOLUTE_MAX_CONFIDENCE
    assert apply_confidence_cap(2.0) <= ABSOLUTE_MAX_CONFIDENCE
    assert apply_confidence_cap(-1.0) == 0.0


def test_confidence_cap_object() -> None:
    cap = ConfidenceCap()
    assert cap.apply(1.0) <= ABSOLUTE_MAX_CONFIDENCE
    assert cap.violates_absolute(1.0) is True
    assert cap.violates_absolute(0.5) is False
    result = cap.calibrate(1.0)
    assert result.was_capped is True
    assert result.calibrated <= ABSOLUTE_MAX_CONFIDENCE


# --- episode + store ---------------------------------------------------------

def test_episode_clamps_severity() -> None:
    ep = SomaticEpisode(severity_peak=5.0)
    assert ep.severity_peak == 1.0


def test_episode_richness_and_breadth() -> None:
    ep = SomaticEpisode(
        signal_types=["a", "b", "c", "d"],
        environmental_signature={"x": 1, "y": 2, "z": 3, "w": 4},
    )
    assert ep.signature_richness == 1.0
    assert ep.signal_breadth == 1.0
    empty = SomaticEpisode()
    assert empty.signature_richness == 0.0
    assert empty.signal_breadth == 0.0


def test_episode_store_bounded() -> None:
    store = SomaticEpisodeStore(max_episodes=2)
    for i in range(5):
        store.store(SomaticEpisode(signal_types=[f"s{i}"]))
    assert store.count == 2
    assert store.fill_ratio == 1.0


# --- resonance / risk / forecast --------------------------------------------

def test_environmental_resonance_unit_bounded() -> None:
    res = EnvironmentalResonance()
    ep = SomaticEpisode(severity_peak=0.6, environmental_signature={"host": "a"})
    out = res.apply(ep)
    assert 0.0 <= out.resonance_score <= 1.0


def test_risk_projection_capped() -> None:
    proj = EnvironmentalRiskProjector()
    ep = SomaticEpisode(signal_types=["a", "b", "c"], severity_peak=1.0)
    r = proj.project_from_episode(ep)
    assert r.risk_score <= RISK_CEILING
    assert r.risk_score <= 0.85


def test_somatic_forecast_unit_bounded() -> None:
    ep = SomaticEpisode(signal_types=["temp"], severity_peak=0.5)
    pt = SomaticForecast().forecast_episode(ep)
    assert 0.0 <= pt.resonance_projected <= 1.0


def test_precursor_resonance_forecast_list() -> None:
    ep = SomaticEpisode(signal_types=["vib"], severity_peak=0.5)
    sigs = [
        PrecursorSignal(pattern_id="p1", strength=0.6, domain="somatic"),
        PrecursorSignal(pattern_id="p2", strength=0.9, domain="somatic"),
    ]
    results = PrecursorResonanceForecaster().forecast(ep, sigs)
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(0.0 <= p.projected_resonance <= 1.0 for p in results)
    assert PrecursorResonanceForecaster().forecast(ep, []) == []


# --- calibration -------------------------------------------------------------

def test_environmental_uncertainty_positive() -> None:
    eu = EnvironmentalUncertainty()
    assert eu.report(count=2).mean_spread > 0
    # more samples -> narrower spread, but never zero
    assert eu.report(count=100).mean_spread > 0
    assert eu.report(count=2).mean_spread > eu.report(count=100).mean_spread


def test_precursor_reliability_capped() -> None:
    pr = PrecursorReliability()
    sig = PrecursorSignal(pattern_id="p1", strength=0.99, domain="telemetry")
    assert pr.score(sig).reliability <= ABSOLUTE_MAX_CONFIDENCE


def test_somatic_confidence_capped() -> None:
    ep = SomaticEpisode(severity_peak=0.95, environmental_signature={"a": 1, "b": 2})
    sc = SomaticConfidenceCalibrator().from_episode(ep)
    assert sc.calibrated <= ABSOLUTE_MAX_CONFIDENCE


# --- runtime path ------------------------------------------------------------

def _signal(value: float = 0.8) -> AttentionSignal:
    return AttentionSignal(
        signal_id="s1",
        source_domain="somatic",
        signal_type="hrv_drop",
        raw_value=value,
        timestamp=datetime.now(timezone.utc),
    )


def test_runtime_somatic_submit() -> None:
    kernel = AttentionKernel(max_focus=5, max_queue=20)
    rt = RuntimeSomaticAttention(kernel, stress=0.3)
    assert rt.stress == pytest.approx(0.3)
    result = rt.submit_signal(_signal())
    assert result["accepted"] is True


def test_somatic_runtime_bridge_payload() -> None:
    kernel = AttentionKernel(max_focus=5, max_queue=20)
    bridge = SomaticRuntimeBridge(RuntimeSomaticAttention(kernel))
    r = bridge.from_payload({"severity": 0.7, "stress": 0.4})
    assert r["accepted"] is True
    assert bridge.runtime.stress == pytest.approx(0.4)
