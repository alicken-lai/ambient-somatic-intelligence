# v0.5.2 Attention Memory Consolidation Gate

**Version:** `0.5.2`  
**Date:** 2026-05-19  
**Base:** v0.5.1-alpha RUNTIME-ATTENTIVE

## Gate Criteria

| Phase | Criterion | Target | Module |
|-------|-----------|--------|--------|
| 0 | Read-only audit | Present | `v052/audit/` |
| 1 | Consolidation core | Bounded store + trace | `attention/consolidation/` |
| 2 | Somatic episodes | Resonance + cap | `attention/somatic/` |
| 3 | Reinforcement / decay | No runaway feedback | `attention/consolidation/` |
| 4 | Noise suppression | Benign patterns | `attention/consolidation/` |
| 5 | Runtime bridge | Kernel wire | `attention/runtime/` |
| 6 | Explainability | Consolidation reports | `attention/explainability/` |
| 7 | Observability v052 | 5 metrics + stability | `observability/v052/` |
| 8 | Simulated windows | 1d/7d/30d/90d | `v052/reports/` |
| 9 | Tests | 10 areas | `tests/v052/` |
| 10 | AttentionMemoryStabilityScore | ≥ 0.90 | `observability/v052/attention_memory_stability_score.py` |
| 11 | Release doc | This file | `docs/releases/v052_attention_memory_gate.md` |

## Memory Stability (Phase 10)

Extends v0.5.1 `RuntimeAttentionStabilityScore` with:

| Memory dimension | Weight |
|------------------|--------|
| consolidation_headroom | 0.06 |
| precursor_memory_health | 0.05 |
| noise_suppression | 0.05 |
| trace_discipline | 0.04 |

**Gate threshold:** 0.90 (combined with runtime + base attention)

## Execution

```bash
python3 -m pytest tests/v052/ tests/v051/ tests/v050/ -q
python3 -c "from v052_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v052/reports/attention_memory_timeseries.json'))"
```

## Constraints honored

- No ML reinforcement, no unbounded memory growth
- No ontology / replay / Guardian doctrine changes
- v0.5.0 kernel + v0.5.1 runtime attention preserved
- `memory/somatic/sensor_episode_store.py` remains persistent SSOT

## Overall Gate Verdict

Run `pytest tests/v052/ tests/v051/ tests/v050/ -q` and `evaluate_attention_memory_stability()` with clean bridge evidence to confirm **PASS**.
