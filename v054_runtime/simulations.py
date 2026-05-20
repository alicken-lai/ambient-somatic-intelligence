"""Accelerated calibration simulations (24h/7d/30d/90d)."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attention.calibration.confidence_cap import ABSOLUTE_MAX_CONFIDENCE
from attention.calibration.forecast_confidence import ForecastConfidenceCalibrator
from attention.core.attention_target import AttentionTarget
from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.calibrated_attention_activation import CalibratedAttentionActivation
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from attention.somatic.somatic_episode import SomaticEpisode
from attention.somatic.somatic_confidence import SomaticConfidenceCalibrator
from observability.v054.calibration_stability_score import (
    evaluate_calibration_stability,
    evidence_from_calibrated_forecaster,
)


@dataclass
class CalibrationWindowParams:
    name: str
    simulated_hours: float
    cycles: int = 80
    somatic_episodes: int = 10


WINDOWS: dict[str, CalibrationWindowParams] = {
    "24h": CalibrationWindowParams("24h", 24, cycles=100, somatic_episodes=12),
    "7d": CalibrationWindowParams("7d", 7 * 24, cycles=250, somatic_episodes=25),
    "30d": CalibrationWindowParams("30d", 30 * 24, cycles=400, somatic_episodes=40),
    "90d": CalibrationWindowParams("90d", 90 * 24, cycles=500, somatic_episodes=55),
}


def simulate_window(params: CalibrationWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    store_cap = max(500, params.cycles + 200)
    store = AttentionMemoryStore(max_entries=store_cap)
    bridge = RuntimeAttentionMemoryBridge(kernel=kernel, store=store)
    forecaster = AttentionForecast(
        kernel=kernel,
        store=bridge.store,
        precursor_memory=bridge.precursor_memory,
    )
    activation = CalibratedAttentionActivation(kernel=kernel, store=bridge.store)
    calibrator = ForecastConfidenceCalibrator()
    somatic_cal = SomaticConfidenceCalibrator()

    target_id = f"cal-sim-{params.name}"
    calibrated_series: list[float] = []

    for i in range(params.cycles):
        t = AttentionTarget(
            source_domain="somatic" if i % 6 == 0 else "telemetry",
            signal_type=f"cal-sim-{i % 20}",
            raw_value=0.35 + (i % 8) * 0.07,
            metadata={"tags": [f"cal-{i % 5}"]},
        )
        bridge.ingest_target(t)
        forecaster.ingest(t)
        if i % 12 == 0:
            r = forecaster.forecast(target_id, "24h")
            for p in r.projections:
                cal = calibrator.calibrate(p.band.confidence, band_width=p.band.width())
                calibrated_series.append(cal.calibrated)
        if i % 20 == 0:
            activation.submit_calibrated_target(t, raw_confidence=0.72 + (i % 5) * 0.04)
        if i % 25 == 0:
            kernel.tick()

    for j in range(params.somatic_episodes):
        ep = SomaticEpisode(
            signal_types=[f"som-cal-{j % 4}"],
            severity_peak=0.3 + (j % 5) * 0.1,
            environmental_signature={"zone": "lab", "band": str(j % 3)},
        )
        sc = somatic_cal.from_episode(ep)
        calibrated_series.append(sc.calibrated)

    evidence = evidence_from_calibrated_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=params.cycles // 12
    )
    report = evaluate_calibration_stability(evidence=evidence, forecaster=forecaster, bridge=bridge)

    max_conf = max(calibrated_series) if calibrated_series else 0.0
    return {
        "window": params.name,
        "simulated_hours": params.simulated_hours,
        "cycles": params.cycles,
        "mean_calibrated_confidence": statistics.mean(calibrated_series) if calibrated_series else 0.85,
        "max_calibrated_confidence": max_conf,
        "below_absolute_max": max_conf <= ABSOLUTE_MAX_CONFIDENCE,
        "stability_score": report.calibration_score,
        "gate_pass": report.gate_pass,
    }


def run_all_windows() -> dict[str, Any]:
    results = {name: simulate_window(p) for name, p in WINDOWS.items()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "windows": results,
        "overall_gate_pass": all(r["gate_pass"] for r in results.values()),
        "absolute_max_confidence": ABSOLUTE_MAX_CONFIDENCE,
    }


def write_timeseries(out_path: Path) -> dict[str, Any]:
    data = run_all_windows()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
