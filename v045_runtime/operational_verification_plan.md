# v0.4.5 Operational Runtime Verification Plan

**Version:** `0.4.5-alpha`  
**Base:** v0.4 lineage COMPLETE · v0.45 stability semantics PASS · clean graph score 1.0  
**Date:** 2026-05-19

## Purpose

Validate that Ambient OS subsystems remain **operationally stable** under sustained runtime load without lowering gates, auto-repairing state, or changing ontology/promotion/telemetry scoring.

## Simulated vs Live Soak

| Mode | What it proves | Limitation |
|------|----------------|--------------|
| **Accelerated simulation** (this gate) | Deterministic wire/unwire, entropy sampling, trace caps, replay hashes at scaled iteration counts (`runtime_test_matrix.json`) | Does not capture OS scheduler jitter, disk I/O stalls, or network partitions |
| **Live daemon soak** (recommended post-gate) | Real `dmn_tick_status`, maturation daily reports, circadian continuity over 72h+ | Requires dedicated host; not runnable in a single IDE session |

**Policy:** Gate PASS uses **72h window parameters** in accelerated mode. Production soak unlock is **recommended** after gate PASS, not substituted by simulation.

### Window mapping (accelerated)

| Window | Simulated minutes | Entropy samples | Wire cycles | Daemon ticks |
|--------|-------------------|-----------------|-------------|--------------|
| 1h | 60 | 12 | 20 | 12 |
| 6h | 360 | 72 | 60 | 72 |
| 24h | 1440 | 288 | 120 | 288 |
| **72h (gate)** | 4320 | 864 | 240 | 864 |

Each sample/tick ≈ **5 simulated minutes** (`tick_minutes` in matrix).

## Phases

| Phase | Artifact | PASS criteria |
|-------|----------|---------------|
| 0 | This plan + matrix + targets | Artifacts present |
| 1 | `reports/entropy_runtime_report.md` | max entropy < 0.30, no exponential drift |
| 2 | `reports/patch_runtime_report.md` | leakage=0, duplicate=0, 100% unwire repro |
| 3 | `reports/isolation_runtime_report.md` | parallel contexts, sandbox containment |
| 4 | `reports/authority_trace_runtime_report.md` | ring buffer cap honored, no runaway |
| 5 | `reports/daemon_runtime_report.md` | tick status ok, maturation continuity |
| 6 | `reports/truthgraph_runtime_report.md` | stability ≥ 0.85 over simulated time |
| 7 | `reports/replay_runtime_report.md` | replay hash match rate 1.0 |
| 8 | `operational_stability_score.py` | composite ≥ 0.90, 7 dimensions |
| 9 | `reports/failure_mode_simulation.md` | 7 injections, recovery without corruption |
| 10 | `docs/releases/v045_operational_runtime_gate.md` | all criteria PASS |

## Constraints (non-negotiable)

- NO ontology/promotion/verifier/telemetry scoring changes
- NO threshold lowering, NO auto-repair runtime state
- NO architecture/doctrine redesign
- Preserve TruthGraph, EntropyController, IsolationKernel, PatchRegistry

## Execution

```bash
python3 v045_runtime/run_operational_verification.py
python3 -m pytest tests/v045/ tests/v045_runtime/ tests/v043/ tests/v042/ -q
```

## Entry harness

`v045_runtime/run_operational_verification.py` — single entry; emits all phase reports and `reports/operational_stability_summary.json`.
