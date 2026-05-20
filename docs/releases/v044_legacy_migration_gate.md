# v0.4.4 Legacy Mutation Migration — Release Gate

**Version:** `0.4.4-alpha`  
**Date:** 2026-05-18  
**Base:** v0.4.3-alpha (Isolation PASS, 857 legacy mutation paths in v043 audit metadata)

## Verdict: **PARTIAL**

Infrastructure and critical-path hooks are in place; full legacy path migration is **not** complete. Gate thresholds (≥95% coverage, ≥0.90 migration score) are **not** met — by design this release reports honest metrics rather than aspirational PASS.

## Gate Criteria

| Criterion | Target | Result |
|-----------|--------|--------|
| Legacy mutation inventory | Complete classification | **PASS** — `v044/audit/legacy_mutation_inventory.json` (500 catalogued / 857 scanned) |
| Guard infrastructure (5 categories) | All present | **PASS** — `GuardedFileWriter`, `SingletonGuard`, `GuardedCallback`, `RegistryGuard`, coverage scanner |
| Critical path migration | Memory, governance audit, skill registry, bus callbacks | **PARTIAL** — opt-in `execution_context` / guarded APIs; legacy paths unchanged by default |
| Migration coverage | ≥ 0.95 | **FAIL** — **7.2%** (36 / 500 catalogued paths) |
| Migration score | ≥ 0.90 | **FAIL** — **0.570** (classification: `partial`) |
| pytest `tests/v044/` | Green | **PASS** — 12 passed |
| pytest `tests/v043/` regression | Green | **PASS** — 21 passed |
| pytest `tests/v042/` regression | Green | **PASS** — 12 passed |

## Inventory (Phase 0)

| Category | Count |
|----------|-------|
| FILE_WRITE | 468 |
| CALLBACK_MUTATION | 22 |
| REGISTRY_MUTATION | 10 |
| SINGLETON_MUTATION | 0 |
| UNKNOWN | 0 |

**Note:** v043 `execution_authority_audit.json` lists `total_scanned_mutations: 857` but only **500** detailed `mutation_paths` rows. Coverage and score use catalogued paths; honesty note is embedded in `compute_migration_coverage()`.

## Migration Coverage (Phase 6)

```json
{
  "catalogued_paths": 500,
  "total_scanned_mutations": 857,
  "migrated_paths": 36,
  "coverage_ratio": 0.072,
  "gate_pass": false,
  "by_category": {
    "FILE_WRITE": { "coverage": 0.0299 },
    "CALLBACK_MUTATION": { "coverage": 1.0 },
    "REGISTRY_MUTATION": { "coverage": 0.0 }
  }
}
```

## Migration Score (Phase 9)

```json
{
  "score": 0.5702,
  "classification": "partial",
  "gate_pass": false,
  "dimensions": {
    "mutation_coverage": 0.072,
    "authority_infrastructure": 1.0,
    "rollback_readiness": 1.0,
    "trace_coverage": 0.3,
    "regression_stability": 1.0
  }
}
```

Probe:

```bash
python3 -c "
from observability.v04.migration_coverage import compute_migration_coverage
from observability.v04.migration_score import evaluate_migration
print('coverage', compute_migration_coverage().to_dict())
print('score', evaluate_migration().to_dict())
"
```

## pytest

```bash
python3 -m pytest tests/v044/ tests/v043/ tests/v042/ -q
```

```text
tests/v044/: 12 passed
tests/v043/: 21 passed
tests/v042/: 12 passed
```

## Files Created

### Audit (`v044/audit/`)

- `build_inventory.py`, `generate_migration_reports.py`
- `legacy_mutation_inventory.json`
- `mutation_classification_report.md`
- `unknown_mutation_report.json`
- `file_write_migration_report.json`

### Kernel isolation

- `kernel/isolation/guarded_file_writer.py`
- `kernel/isolation/singleton_guard.py`, `singleton_mutation.py`
- `kernel/isolation/guarded_callback.py`
- `kernel/isolation/registry_guard.py`, `registry_mutation.py`

### Observability

- `observability/v04/migration_coverage.py`
- `observability/v04/migration_score.py`
- `observability/v04/authority_trace.py` — `record_guarded_operation()`

### Critical-path hooks (opt-in)

- `governance/audit_log.py` — guarded append when `execution_context` provided
- `memory/memory_kernel.py` — guarded `store()` when `execution_context` provided
- `skills/core/skill_registry.py` — `RegistryGuard` when `execution_context` provided
- `somatic/signal_bus.py` — `on_guarded()`

### Tests

- `tests/v044/` (12 tests, 8 areas)

## Top Remaining Unmigrated Risks

1. **468 FILE_WRITE paths** — mostly implicit `append` across runtime/memory/telemetry; only modules with guard markers count as migrated (~3%).
2. **High-risk governance_audit writes** — e.g. `runtime/isolation_kernel/execution_sandbox.py`, `integration/v04_wiring.py`, ontology promotion paths still implicit.
3. **REGISTRY_MUTATION (10 paths)** — `PatchRegistry` / `TruthRegistry` not yet wired to `RegistryGuard` at call sites.
4. **857 vs 500 catalog gap** — expand v043 audit detail rows or re-scan repo before claiming full-surface coverage.
5. **Opt-in only** — legacy callers without `ExecutionContext` still use unguarded I/O (backward compatible).

## Follow-up Plan

1. Batch-migrate FILE_WRITE in `runtime/`, `memory/`, `governance/` using `GuardedFileWriter`.
2. Wire `RegistryGuard` into `kernel/wiring/patch_registry.py` and `kernel/truth/truth_registry.py`.
3. Re-run `build_inventory.py` after expanding v043 audit to full 857 path detail.
4. Raise `trace_coverage` by connecting `AuthorityTrace` to all guard entry points.
5. Re-evaluate gate when `coverage_ratio >= 0.95` and `migration_score >= 0.90`.

## Preserved (unchanged)

TruthGraph, EntropyController, PatchRegistry semantics, ExecutionContext/WriteGuard/Sandbox/RollbackBoundary, Guardian, ontology/promotion/verifier/telemetry scoring.
