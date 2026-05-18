# Mutation Surface Report (v0.4.3)

**Generated:** 2026-05-18T13:24:34.576744+00:00

## Summary

| Metric | Value |
|--------|-------|
| Mutation paths scanned | 857 |
| Write targets identified | 6 |
| Callback registrations | 12 |

## High-Risk Surfaces

- `runtime/isolation_kernel/execution_sandbox.py:125` → `governance_audit` (implicit)
- `runtime/isolation_kernel/execution_sandbox.py:271` → `governance_audit` (implicit)
- `runtime/entropy_controller/decay_enforcer.py:133` → `memory/dmn.jsonl` (implicit)
- `runtime/evolution_engine/patch_proposer.py:125` → `governance_audit` (implicit)
- `kernel/integration_bus.py:1221` → `governance_audit` (implicit)
- `kernel/integration_bus.py:1269` → `governance_audit` (implicit)
- `kernel/integration_bus.py:1398` → `truth_graph` (implicit)
- `kernel/integration_bus.py:1433` → `truth_graph` (implicit)
- `kernel/integration_bus.py:1482` → `governance_audit` (implicit)
- `kernel/integration_bus.py:1577` → `truth_graph` (implicit)
- `integration/v04_wiring.py:243` → `governance_audit` (implicit)
- `integration/v04_wiring.py:510` → `governance_audit` (implicit)
- `memory/ontology/strategic_write_gate.py:69` → `governance_audit` (implicit)
- `memory/ontology/strategic_write_gate.py:228` → `governance_audit` (implicit)
- `memory/ontology/promotion_guard.py:249` → `governance_audit` (implicit)
- `memory/ontology/promotion_engine.py:151` → `governance_audit` (implicit)
- `memory/ontology/promotion_engine.py:287` → `governance_audit` (implicit)
- `memory/ontology/promotion_engine.py:311` → `governance_audit` (implicit)
- `governance/tool_permissions.py:260` → `governance_audit` (implicit)
- `governance/tool_permissions.py:273` → `governance_audit` (implicit)
- `agents/skillify/skill_candidate_validator.py:113` → `governance_audit` (implicit)
- `telemetry/runtime/clock_sync.py:170` → `governance_audit` (implicit)
- `telemetry/maturation/p17d_analyze.py:190` → `governance_audit` (implicit)
- `somatic/attention_manager.py:221` → `governance_audit` (implicit)
- `somatic/attention_runtime/attention_engine.py:244` → `governance_audit` (implicit)
- `somatic/attention_runtime/stress_scorer.py:303` → `governance_audit` (implicit)

## Recommendations

1. Route all writes through `WriteGuard` + `RootResolver`
2. Require `ExecutionContext` for governed writes
3. Register bus callbacks via `CallbackGuard`
