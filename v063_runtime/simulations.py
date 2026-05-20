"""Accelerated coherence stress simulations (24h/7d/30d/90d/180d)."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.forecasting.attention_forecast import AttentionForecast
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.cognition.cognitive_governor import CognitiveGovernor
from observability.v063.cognitive_coherence_stability_score import (
    evaluate_cognitive_coherence_stability,
    evidence_from_coherence_forecaster,
)


@dataclass
class CoherenceWindowParams:
    name: str
    simulated_hours: float
    cycles: int = 80


WINDOWS: dict[str, CoherenceWindowParams] = {
    "24h": CoherenceWindowParams("24h", 24, cycles=100),
    "7d": CoherenceWindowParams("7d", 7 * 24, cycles=250),
    "30d": CoherenceWindowParams("30d", 30 * 24, cycles=400),
    "90d": CoherenceWindowParams("90d", 90 * 24, cycles=500),
    "180d": CoherenceWindowParams("180d", 180 * 24, cycles=600),
}


def simulate_window(params: CoherenceWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    store = AttentionMemoryStore(max_entries=max(500, params.cycles + 200))
    bridge = RuntimeAttentionMemoryBridge(kernel=kernel, store=store)
    forecaster = AttentionForecast(
        kernel=kernel,
        store=bridge.store,
        precursor_memory=bridge.precursor_memory,
    )
    governor = CognitiveGovernor()
    coherence_series: list[float] = []

    for i in range(params.cycles):
        meta: dict[str, Any] = {"tags": [f"coh-{i % 5}"]}
        if i % 11 == 0:
            meta["replay_derived"] = True
            meta["replay_labeled"] = True
        if i % 17 == 0:
            meta["synthetic_projection"] = True
            meta["synthetic_labeled"] = True
        t = AttentionTarget(
            source_domain="memory" if i % 9 == 0 else "telemetry",
            signal_type=f"coh-sim-{i % 20}",
            raw_value=0.35 + (i % 8) * 0.07,
            metadata=meta,
        )
        bridge.ingest_target(t)
        forecaster.ingest(t)
        d = governor.govern_target(
            t,
            raw_confidence=0.72 if i % 18 == 0 else 0.75,
            replay_hint=0.2 if i % 11 == 0 else 0.0,
        )
        coherence_series.append(d.coherence_score)

    evidence = evidence_from_coherence_forecaster(
        forecaster, bridge=bridge, submissions=params.cycles // 12
    )
    report = evaluate_cognitive_coherence_stability(
        evidence=evidence, forecaster=forecaster, bridge=bridge
    )
    return {
        "window": params.name,
        "simulated_hours": params.simulated_hours,
        "cycles": params.cycles,
        "mean_coherence_score": (
            statistics.mean(coherence_series) if coherence_series else 1.0
        ),
        "coherence_score": report.coherence_score,
        "gate_pass": report.gate_pass,
    }


def run_all_windows() -> dict[str, Any]:
    results = {name: simulate_window(p) for name, p in WINDOWS.items()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.6.3",
        "windows": results,
        "overall_gate_pass": all(r["gate_pass"] for r in results.values()),
    }


def write_timeseries(out_path: Path) -> dict[str, Any]:
    data = run_all_windows()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
