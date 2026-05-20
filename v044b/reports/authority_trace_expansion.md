# Authority Trace Expansion (v0.4.4B Phase 4)

## Coverage

| Metric | Before (v0.4.4α) | After (v0.4.4B) | Target |
|--------|------------------|-----------------|--------|
| Trace dimension | ~0.30 | **1.00** | ≥ 0.70 |

## Instrumented paths

- `RegistryGuard.mutate()` → `REGISTRY_MUTATION`
- `GovernedMemoryWriter` → `MEMORY_WRITE`
- `GovernanceAuditLog._append_record()` → `FILE_WRITE` (governed)
- `GuardedFileWriter` → existing `guarded_mutation`
- `GuardedCallback.register()` → `CALLBACK_MUTATION`

## Silent write detection

`tests/v044b/test_authority_trace.py` asserts guarded operations emit `mutation_type` on trace events.
