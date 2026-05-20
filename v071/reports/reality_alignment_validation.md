# Reality Alignment Validation (v0.7.1)

**Generated:** 2026-05-19  
**Gate:** `CognitiveRealityAlignmentScore` ≥ 0.90

## Validation summary

| Check | Status |
|-------|--------|
| Phase 0 audit artifacts | Present under `v071/audit/` |
| Governance reality modules | `governance/reality/` (phases 1–5) |
| Explainability (3) | `attention/explainability/` reality modules |
| Observability v071 | 6 metrics + composite score |
| Governor wiring | `reality_alignment_observability` after civilization |
| Stress scenarios (7) | `v071_runtime/simulations.py` |
| Horizons (5) | 24h / 7d / 30d / 90d / 180d in timeseries |

## Constraints verified

- No forced consensus or sovereign reality merge
- No centralized truth authority or hidden truth override
- Guardian and constitutional paths unchanged
- Kernel TruthGraph not redesigned (read/compare only)

## Execution

```bash
python3 -m pytest tests/v071/ tests/v070/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q
python3 -c "from observability.v071.cognitive_reality_alignment_score import evaluate_cognitive_reality_alignment as e; r=e(); print(r.reality_alignment_score, r.gate_pass)"
python3 -c "from v071_runtime.simulations import write_timeseries; from pathlib import Path; write_timeseries(Path('v071/reports/cross_runtime_reality_timeseries.json'))"
```
