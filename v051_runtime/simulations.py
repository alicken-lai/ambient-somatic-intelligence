"""Accelerated attention runtime simulations (1h/6h/24h/72h windows)."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attention.core.attention_target import AttentionTarget
from attention.governance.guardian_attention_bridge import GuardianAttentionBridge
from attention.kernel.attention_kernel import AttentionKernel
from attention.runtime.attention_pressure_controller import AttentionPressureController
from attention.runtime.overload_recovery import OverloadRecovery
from attention.runtime.telemetry_attention_adapter import TelemetryAttentionAdapter
from attention.runtime.telemetry_attention_signal import telemetry_to_target
from observability.v051.runtime_attention_stability_score import (
    evidence_from_kernel,
    evaluate_runtime_attention_stability,
)
from telemetry.core.telemetry_schema import TelemetryRecord


@dataclass
class AttentionWindowParams:
    name: str
    simulated_minutes: int
    telemetry_samples: int = 120
    governance_events: int = 8
    somatic_spikes: int = 5
    memory_activations: int = 10
    tick_cycles: int = 60


WINDOWS: dict[str, AttentionWindowParams] = {
    "1h": AttentionWindowParams("1h", 60, telemetry_samples=30, tick_cycles=15),
    "6h": AttentionWindowParams("6h", 360, telemetry_samples=90, tick_cycles=45),
    "24h": AttentionWindowParams("24h", 1440, telemetry_samples=200, tick_cycles=120),
    "72h": AttentionWindowParams("72h", 4320, telemetry_samples=400, tick_cycles=240),
}


def _make_record(i: int, category: str = "attention") -> TelemetryRecord:
    return TelemetryRecord(
        source="v051_sim",
        timestamp=datetime.now(timezone.utc).isoformat(),
        category=category,
        payload={"salience": 0.4 + (i % 10) * 0.05, "signal_type": f"sim-{i}"},
        confidence=0.95,
    )


def simulate_window(params: AttentionWindowParams) -> dict[str, Any]:
    kernel = AttentionKernel(max_focus=8, max_queue=50)
    adapter = TelemetryAttentionAdapter(kernel)
    guardian = GuardianAttentionBridge(kernel)
    pressure = AttentionPressureController(kernel)
    recovery = OverloadRecovery(kernel)

    accepted = 0
    for i in range(params.telemetry_samples):
        r = _make_record(i, "attention" if i % 3 else "somatic")
        if adapter.ingest(r).get("accepted"):
            accepted += 1
        if i % 20 == 0:
            guardian.from_guardian_result("sim action", "REVIEW_REQUIRED", matched=["sim"])
        if i % 10 == 0:
            kernel.tick()

    # Drain queue and stabilize focus before pressure sampling
    for _ in range(max(3, params.tick_cycles // 20)):
        kernel.tick()
        kernel.apply_decay()

    pressure_series: list[float] = []
    for _ in range(max(3, params.tick_cycles // 10)):
        d = pressure.evaluate()
        pressure_series.append(d.pressure.composite)
        kernel.tick()
        recovery.step()

    evidence = evidence_from_kernel(kernel, submissions=accepted)
    report = evaluate_runtime_attention_stability(evidence=evidence, kernel=kernel)

    return {
        "window": params.name,
        "simulated_minutes": params.simulated_minutes,
        "telemetry_samples": params.telemetry_samples,
        "accepted_submissions": accepted,
        "mean_pressure": statistics.mean(pressure_series) if pressure_series else 0.0,
        "max_pressure": max(pressure_series) if pressure_series else 0.0,
        "stability_score": report.runtime_score,
        "gate_pass": report.gate_pass,
        "pressure_tail": pressure_series[-5:] if len(pressure_series) >= 5 else pressure_series,
    }


def run_all_windows() -> dict[str, Any]:
    results = {name: simulate_window(params) for name, params in WINDOWS.items()}
    all_pass = all(r["gate_pass"] for r in results.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "windows": results,
        "overall_gate_pass": all_pass,
    }


def write_timeseries(out_path: Path) -> dict[str, Any]:
    data = run_all_windows()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
