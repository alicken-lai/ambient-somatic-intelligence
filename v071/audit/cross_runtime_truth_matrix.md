# Cross-Runtime Truth Matrix (v0.7.1)

| From \ To | ambient | hermes | foreign |
|-----------|---------|--------|---------|
| ambient | local canonical ops | orchestration read | advisory compare |
| hermes | client routing | local ops | advisory compare |
| foreign | labeled observational | labeled observational | peer-local only |

## Exchange rules

1. **No merge** — `DivergenceRecord.merge_forbidden` always true
2. **Provenance required** — `provenance_truth_exchange.py`
3. **Foreign label** — `foreign_truth_label.py` trust tier observational
4. **Kernel TruthGraph** — read/compare only; no sovereign override redesign

## Governor attachment order

`runtime_external_observability` → `civilization_observability` → `reality_alignment_observability`
