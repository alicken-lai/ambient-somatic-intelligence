"""Accelerated attention memory consolidation simulations (1d/7d/30d/90d)."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attention.consolidation.attention_memory_store import AttentionMemoryStore
from attention.consolidation.attention_trace import AttentionTrace
from attention.core.attention_target import AttentionTarget
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.runtime_attention_memory_bridge import RuntimeAttentionMemoryBridge
from attention.somatic.environmental_resonance import EnvironmentalResonance
from attention.somatic.somatic_episode import SomaticEpisode
from observability.v052.attention_memory_stability_score import (
    evaluate_attention_memory_stability,
    evidence_from_bridge,
)


@dataclass
class MemoryWindowParams:
    name: str
    simulated_days: int
    consolidation_cycles: int = 60
    somatic_episodes: int = 10


WINDOWS: dict[str, MemoryWindowParams] = {
    "1d": MemoryWindowParams("1d", 1, consolidation_cycles=40, somatic_episodes=5),
    "7d": MemoryWindowParams("7d", 7, consolidation_cycles=120, somatic_episodes=15),
    "30d": MemoryWindowParams("30d", 30, consolidation_cycles=300, somatic_episodes=30),
    "90d": MemoryWindowParams("90d", 90, consolidation_cycles=500, somatic_episodes=50),
}


def simulate_window(params: MemoryWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    store_cap = max(500, params.consolidation_cycles + 200)
    store = AttentionMemoryStore(max_entries=store_cap)
    bridge = RuntimeAttentionMemoryBridge(kernel=kernel, store=store)
    resonance = EnvironmentalResonance()

    consolidations = 0
    for i in range(params.consolidation_cycles):
        t = AttentionTarget(
            source_domain="somatic" if i % 4 == 0 else "telemetry",
            signal_type=f"mem-sim-{i % 20}",
            raw_value=0.35 + (i % 8) * 0.07,
            metadata={"tags": [f"tag-{i % 5}"]},
        )
        bridge.ingest_target(t)
        if i % 7 == 0:
            bridge.activate_consolidated(t.target_id, t.source_domain, float(t.raw_value))
            consolidations += 1
        if i % 12 == 0:
            kernel.tick()
            kernel.apply_decay()
        if i % 40 == 0 and i > 0:
            store.trace = AttentionTrace(max_entries=store.trace.max_entries)

    for j in range(params.somatic_episodes):
        ep = SomaticEpisode(
            signal_types=[f"sig-{j % 3}"],
            severity_peak=0.3 + (j % 5) * 0.1,
            environmental_signature={"room": "lab", "band": str(j % 4)},
        )
        resonance.apply(ep)

    pressure_series: list[float] = []
    from observability.v052.memory_consolidation_pressure import compute_memory_consolidation_pressure

    for _ in range(max(3, params.consolidation_cycles // 20)):
        p = compute_memory_consolidation_pressure(store)
        pressure_series.append(p.composite)

    evidence = evidence_from_bridge(bridge, kernel=kernel, submissions=consolidations)
    report = evaluate_attention_memory_stability(evidence=evidence, bridge=bridge, kernel=kernel)

    return {
        "window": params.name,
        "simulated_days": params.simulated_days,
        "consolidation_cycles": params.consolidation_cycles,
        "consolidations": consolidations,
        "memory_count": store.count,
        "mean_pressure": statistics.mean(pressure_series) if pressure_series else 0.0,
        "stability_score": report.memory_score,
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
