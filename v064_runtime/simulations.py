"""Accelerated meta-cognitive stress simulations (24h/7d/30d/90d/180d)."""

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
from observability.v064.metacognitive_stability_score import (
    evaluate_metacognitive_stability,
    evidence_from_metacognitive_forecaster,
)


@dataclass
class MetacognitiveWindowParams:
    name: str
    simulated_hours: float
    cycles: int = 80


WINDOWS: dict[str, MetacognitiveWindowParams] = {
    "24h": MetacognitiveWindowParams("24h", 24, cycles=100),
    "7d": MetacognitiveWindowParams("7d", 7 * 24, cycles=250),
    "30d": MetacognitiveWindowParams("30d", 30 * 24, cycles=400),
    "90d": MetacognitiveWindowParams("90d", 90 * 24, cycles=500),
    "180d": MetacognitiveWindowParams("180d", 180 * 24, cycles=600),
}


def simulate_window(params: MetacognitiveWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    store = AttentionMemoryStore(max_entries=max(500, params.cycles + 200))
    bridge = RuntimeAttentionMemoryBridge(kernel=kernel, store=store)
    forecaster = AttentionForecast(
        kernel=kernel,
        store=bridge.store,
        precursor_memory=bridge.precursor_memory,
    )
    governor = CognitiveGovernor()
    meta_series: list[float] = []

    for i in range(params.cycles):
        meta: dict[str, Any] = {"tags": [f"meta-{i % 5}"]}
        if i % 13 == 0:
            meta["replay_derived"] = True
        t = AttentionTarget(
            source_domain="memory" if i % 10 == 0 else "telemetry",
            signal_type=f"meta-sim-{i % 20}",
            raw_value=0.38 + (i % 7) * 0.06,
            metadata=meta,
        )
        bridge.ingest_target(t)
        forecaster.ingest(t)
        d = governor.govern_target(
            t,
            raw_confidence=0.74 if i % 19 == 0 else 0.76,
            replay_hint=0.15 if i % 13 == 0 else 0.0,
        )
        meta_series.append(d.metacognition_score)

    evidence = evidence_from_metacognitive_forecaster(
        forecaster, bridge=bridge, submissions=params.cycles // 12
    )
    report = evaluate_metacognitive_stability(
        evidence=evidence, forecaster=forecaster, bridge=bridge
    )
    return {
        "window": params.name,
        "simulated_hours": params.simulated_hours,
        "cycles": params.cycles,
        "mean_metacognition_score": (
            statistics.mean(meta_series) if meta_series else 1.0
        ),
        "metacognition_score": report.metacognition_score,
        "gate_pass": report.gate_pass,
    }


def run_all_windows() -> dict[str, Any]:
    results = {name: simulate_window(p) for name, p in WINDOWS.items()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.6.4",
        "windows": results,
        "overall_gate_pass": all(r["gate_pass"] for r in results.values()),
    }


def write_timeseries(out_path: Path) -> dict[str, Any]:
    data = run_all_windows()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
