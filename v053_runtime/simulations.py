"""Accelerated attention forecast simulations (6h/24h/7d/30d)."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from attention.somatic.environmental_resonance import EnvironmentalResonance
from attention.somatic.somatic_episode import SomaticEpisode
from observability.v053.forecast_stability_score import (
    evaluate_forecast_stability,
    evidence_from_forecaster,
)


@dataclass
class ForecastWindowParams:
    name: str
    simulated_hours: float
    forecast_cycles: int = 60
    somatic_episodes: int = 8


WINDOWS: dict[str, ForecastWindowParams] = {
    "6h": ForecastWindowParams("6h", 6, forecast_cycles=40, somatic_episodes=5),
    "24h": ForecastWindowParams("24h", 24, forecast_cycles=100, somatic_episodes=12),
    "7d": ForecastWindowParams("7d", 7 * 24, forecast_cycles=250, somatic_episodes=25),
    "30d": ForecastWindowParams("30d", 30 * 24, forecast_cycles=400, somatic_episodes=40),
}


def simulate_window(params: ForecastWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    bridge = RuntimeAttentionMemoryBridge(kernel=kernel)
    forecaster = AttentionForecast(kernel=kernel, store=bridge.store, precursor_memory=bridge.precursor_memory)
    resonance = EnvironmentalResonance()

    target_id = f"sim-{params.name}"
    forecasts_run = 0
    for i in range(params.forecast_cycles):
        t = AttentionTarget(
            source_domain="somatic" if i % 5 == 0 else "telemetry",
            signal_type=f"fc-sim-{i % 18}",
            raw_value=0.3 + (i % 7) * 0.08,
            metadata={"tags": [f"fc-{i % 4}"]},
        )
        bridge.ingest_target(t)
        forecaster.ingest(t)
        if i % 10 == 0:
            forecaster.forecast(target_id, params.name if params.name in ("6h", "24h", "7d", "30d") else "24h")
            forecasts_run += 1
        if i % 15 == 0:
            kernel.tick()

    for j in range(params.somatic_episodes):
        ep = SomaticEpisode(
            signal_types=[f"som-{j % 4}"],
            severity_peak=0.25 + (j % 6) * 0.09,
            environmental_signature={"zone": "lab", "band": str(j % 3)},
        )
        resonance.apply(ep)

    confidence_series: list[float] = []
    for wn in ("6h", "24h"):
        r = forecaster.forecast(target_id, wn)
        if r.projections:
            confidence_series.append(sum(p.band.confidence for p in r.projections) / len(r.projections))

    evidence = evidence_from_forecaster(forecaster, bridge=bridge, target_id=target_id, submissions=forecasts_run)
    report = evaluate_forecast_stability(evidence=evidence, forecaster=forecaster, bridge=bridge)

    return {
        "window": params.name,
        "simulated_hours": params.simulated_hours,
        "forecast_cycles": params.forecast_cycles,
        "forecasts_run": forecasts_run,
        "mean_confidence": statistics.mean(confidence_series) if confidence_series else 0.85,
        "stability_score": report.forecast_score,
        "gate_pass": report.gate_pass,
    }


def run_all_windows() -> dict[str, Any]:
    results = {name: simulate_window(p) for name, p in WINDOWS.items()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "windows": results,
        "overall_gate_pass": all(r["gate_pass"] for r in results.values()),
    }


def write_timeseries(out_path: Path) -> dict[str, Any]:
    data = run_all_windows()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
