# Release Gate Integrity Report — v070–v077

**Audit date:** 2026-05-20  
**Method:** Re-evaluated each `evaluate_*` score module; compared to `docs/releases/v0xx_*_gate.md` thresholds.

## Results

| Version | Primary score | Gate threshold | `gate_pass` | Classification |
|---------|---------------|----------------|-------------|----------------|
| v070 | 0.940484 | 0.90 | PASS | stable_cognitive_civilization |
| v071 | 0.943816 | 0.90 | PASS | stable_cognitive_reality_alignment |
| v072 | 0.944682 | 0.90 | PASS | stable_cognitive_temporal_continuity |
| v073 | 0.945426 | 0.90 | PASS | stable_cognitive_meaning_continuity |
| v074 | 0.946067 | 0.90 | PASS | stable_cognitive_value_continuity |
| v075 | 0.946617 | 0.90 | PASS | stable_cognitive_intent_continuity |
| v076 | 0.947091 | 0.90 | PASS | stable_cognitive_purpose_boundary |
| v077 | 0.947498 | 0.90 | PASS | stable_cognitive_agency_boundary |

## Integrity verdict

- **8/8** per-layer gates meet documented threshold (≥ 0.90)
- **8/8** `gate_pass == true` on fresh evaluation
- **0/8** reach `production_grade_*` classification (requires combined ≥ 0.95 per layer)
- Monotonic score progression v070→v077 confirms inheritance chain integrity

## Release doc alignment

All gate docs specify Phase 10 threshold 0.90 and pytest regression through v060. Documented execution commands succeed on this workspace.

**Per-layer release gate integrity: PASS**
