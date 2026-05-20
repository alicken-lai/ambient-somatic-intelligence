# Civilization Lineage Integrity Score

**Evaluator:** `observability/v07x_freeze/civilization_lineage_integrity_score.py`  
**Freeze threshold:** 0.95 (weakest-link across v070–v077 primary scores)

## Aggregate (2026-05-20 evaluation)

| Metric | Value |
|--------|-------|
| **lineage_integrity_score** (min) | **0.940484** |
| mean_lineage_score | 0.945210 |
| min_lineage_score | 0.940484 |
| max_lineage_score | 0.947498 |
| all_layer_gates_pass | true |
| **gate_pass (freeze)** | **false** |
| gap_to_threshold | 0.009516 |
| classification | restricted_civilization_lineage |

## Per-layer scores

| Version | Score | gate_pass (0.90) | Classification |
|---------|-------|------------------|----------------|
| v070 | 0.940484 | true | stable_cognitive_civilization |
| v071 | 0.943816 | true | stable_cognitive_reality_alignment |
| v072 | 0.944682 | true | stable_cognitive_temporal_continuity |
| v073 | 0.945426 | true | stable_cognitive_meaning_continuity |
| v074 | 0.946067 | true | stable_cognitive_value_continuity |
| v075 | 0.946617 | true | stable_cognitive_intent_continuity |
| v076 | 0.947091 | true | stable_cognitive_purpose_boundary |
| v077 | 0.947498 | true | stable_cognitive_agency_boundary |

## Interpretation

All individual release gates **PASS** at 0.90. Freeze gate **FAIL** at 0.95 because weakest-link score (v070 civilization) remains ~0.51% below freeze threshold. Mean score 0.945 is also below 0.95.

No threshold weakening was applied during this audit.

## Reproduce

```bash
PYTHONPATH=. python3 -c "from observability.v07x_freeze.civilization_lineage_integrity_score import evaluate_civilization_lineage_integrity as e; r=e(); print(r.lineage_integrity_score, r.gate_pass)"
PYTHONPATH=. python3 v07x_freeze/freeze_snapshot/evaluator.py
```
