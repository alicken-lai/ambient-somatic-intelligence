"""Accelerated cognitive governance simulations (24h/7d/30d/90d)."""

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
from attention.runtime.governed_attention_activation import GovernedAttentionActivation
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from governance.cognition.salience_arbitrator import SalienceClaim
from observability.v060.cognitive_governance_stability_score import (
    evaluate_cognitive_governance_stability,
    evidence_from_governed_forecaster,
)


@dataclass
class GovernanceWindowParams:
    name: str
    simulated_hours: float
    cycles: int = 80
    arbitration_rounds: int = 10


WINDOWS: dict[str, GovernanceWindowParams] = {
    "24h": GovernanceWindowParams("24h", 24, cycles=100, arbitration_rounds=12),
    "7d": GovernanceWindowParams("7d", 7 * 24, cycles=250, arbitration_rounds=25),
    "30d": GovernanceWindowParams("30d", 30 * 24, cycles=400, arbitration_rounds=40),
    "90d": GovernanceWindowParams("90d", 90 * 24, cycles=500, arbitration_rounds=55),
}


def simulate_window(params: GovernanceWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    store = AttentionMemoryStore(max_entries=max(500, params.cycles + 200))
    bridge = RuntimeAttentionMemoryBridge(kernel=kernel, store=store)
    forecaster = AttentionForecast(
        kernel=kernel,
        store=bridge.store,
        precursor_memory=bridge.precursor_memory,
    )
    governed = GovernedAttentionActivation(kernel=kernel, store=bridge.store)
    target_id = f"gov-sim-{params.name}"
    fairness_series: list[float] = []

    for i in range(params.cycles):
        t = AttentionTarget(
            source_domain="somatic" if i % 7 == 0 else "telemetry",
            signal_type=f"gov-sim-{i % 20}",
            raw_value=0.35 + (i % 8) * 0.07,
            metadata={"tags": [f"gov-{i % 5}"]},
        )
        bridge.ingest_target(t)
        forecaster.ingest(t)
        if i % 18 == 0:
            governed.submit_governed_target(t, raw_confidence=0.72 + (i % 4) * 0.03)
        if i % 25 == 0:
            kernel.tick()

    for j in range(params.arbitration_rounds):
        claims = [
            SalienceClaim("telemetry", 0.4 + (j % 3) * 0.1, 0.8),
            SalienceClaim("somatic", 0.35 + (j % 2) * 0.08, 0.75),
        ]
        out = governed.arbitrate_claims(claims, uncertainty=0.3 + (j % 4) * 0.05)
        fairness_series.append(float(out["arbitration"]["arbitration_fairness"]))

    evidence = evidence_from_governed_forecaster(
        forecaster, bridge=bridge, target_id=target_id, submissions=params.cycles // 12
    )
    report = evaluate_cognitive_governance_stability(
        evidence=evidence, forecaster=forecaster, bridge=bridge
    )

    return {
        "window": params.name,
        "simulated_hours": params.simulated_hours,
        "cycles": params.cycles,
        "mean_arbitration_fairness": statistics.mean(fairness_series) if fairness_series else 0.88,
        "governance_score": report.governance_score,
        "gate_pass": report.gate_pass,
    }


def run_all_windows() -> dict[str, Any]:
    results = {name: simulate_window(p) for name, p in WINDOWS.items()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.6.0",
        "windows": results,
        "overall_gate_pass": all(r["gate_pass"] for r in results.values()),
    }


def write_timeseries(out_path: Path) -> dict[str, Any]:
    data = run_all_windows()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
