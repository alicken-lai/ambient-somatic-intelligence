# v0.5.1 Runtime Attention Integration Gate

**Version:** `0.5.1`  
**Date:** 2026-05-19  
**Base:** v0.5.0-alpha ATTENTIONALLY STABLE

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Read-only audit | Present | `v051/audit/` |
| 1 | Telemetry adapter | Kernel wired | `attention/runtime/` |
| 2 | Governance bridge | Guardian → salience | `attention/governance/` |
| 3 | Memory activation | Bounded cap | `attention/runtime/` |
| 4 | Somatic runtime | Adapter + kernel | `attention/somatic/` |
| 5 | Pressure / recovery | Overload cooldown | `attention/runtime/` |
| 6 | Runtime explainability | No opaque salience | `attention/explainability/` |
| 7 | Observability v051 | Metrics + pressure | `observability/v051/` |
| 8 | Simulated windows | 1h/6h/24h/72h | `v051/reports/` |
| 9 | Tests | 10 areas | `tests/v051/` |
| 10 | RuntimeAttentionStabilityScore | ≥ 0.90 | `observability/v051/runtime_attention_stability_score.py` |
| 11 | Release doc | This file | `docs/releases/v051_runtime_attention_gate.md` |

## Runtime Stability (Phase 10)

Extends v0.5.0 `AttentionStabilityScore` with:

| Runtime dimension | Weight |
|-------------------|--------|
| adapter_health | 0.08 |
| pressure_headroom | 0.07 |

**Gate threshold:** 0.90 (combined with base attention dimensions)

## Execution

```bash
python3 -m pytest tests/v051/ tests/v050/ -q
python3 -c "from v051_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v051/reports/runtime_attention_timeseries.json'))"
```

## Constraints honored

- No ontology / replay / Guardian doctrine changes
- No TruthGraph, Entropy, Isolation, PatchRegistry redesign
- Bounded cognition: activation cap, duplicate guard, overload recovery
- `AttentionKernel` + `KernelSalienceEngine` remain primary orchestrator

## Overall Gate Verdict

Run `pytest tests/v051/ tests/v050/ -q` and `evaluate_runtime_attention_stability()` with clean kernel evidence to confirm **PASS**.
