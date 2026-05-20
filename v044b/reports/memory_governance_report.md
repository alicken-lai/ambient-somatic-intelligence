# Memory Write Governance (v0.4.4B Phase 3)

## `GovernedMemoryWriter`

Path: `kernel/isolation/governed_memory_writer.py`

| API | Target | Trace type |
|-----|--------|------------|
| `append_dmn()` | `WriteTarget.MEMORY` | `MEMORY_WRITE` |
| `append_layer()` | `WriteTarget.MEMORY` | `MEMORY_WRITE` |

## Call sites

- `MemoryKernel.store(execution_context=...)` routes layer writes through `GovernedMemoryWriter`
- `runtime/entropy_controller/decay_enforcer.py` imports `GovernedMemoryWriter` for DMN rotation surface

Legacy DMN append without context remains supported at writer level (`legacy_fallback=True`).
