# v0.4.1 Truth Unification + Reversible Wiring — Release Gate

**Version:** `0.4.1-alpha`  
**Date:** 2026-05-18  
**Scope:** Memory SSOT, retriever unification, reversible patch registry, v04 unwire restoration

## Gate Criteria

| Criterion | Target | Result |
|-----------|--------|--------|
| Memory SSOT conflicts | 0 | **PASS** — `kernel.memory` / `get_memory_kernel()` / `AmbientKernel.memory` share one `MemoryKernel` instance |
| Retriever divergence | 0 | **PASS** — `ContextAssembler` uses injected `KernelRetriever`; no `SemanticRetriever` default in assembler |
| Patch leakage | 0 | **PASS** — `PatchRegistry.restore_phase()` clears `v04_bus` and `v04_integration` patches; somatic `off_any` removes callbacks |
| Wire/unwire reproducibility | 100% | **PASS** — 3× wire/unwire cycles in `tests/v04/test_reversible_wiring.py` |

## pytest (`tests/v04/`)

```text
13 passed in 0.15s
```

Command:

```bash
python3 -m pytest tests/v04/ -q
```

## Changes Summary

### Phase 1 — Memory SSOT

- `kernel/__init__.py`: `get_memory_kernel()` singleton + `_MemoryKernelProxy` module export; removed `context.semantic_retriever` alias for `kernel.memory`
- `AmbientKernel.memory` uses `get_memory_kernel()`

### Phase 2 — Retriever Unification

- `context/assembler.py`: optional `KernelRetriever` injection; default resolves via `get_memory_kernel()`
- `AmbientKernel` wires assembler with `kernel_retriever` (same instance as `context.retriever`)

### Phase 3 — Reversible Wiring Registry

- `kernel/wiring/patch_registry.py`
- `kernel/wiring/patch_handle.py`
- `kernel/wiring/reversible_patch.py`
- `kernel/wiring/__init__.py`

### Phase 4 — v04 Unwire

- `integration/v04_wiring.py`: patches recorded via registry; `unwire_v04(wiring, bus)` restores methods + `bus.unwire_v04()`
- `kernel/integration_bus.py`: `wire_v04` / `unwire_v04` use registry (`v04_bus` phase)
- `integration/v04_kernel_adapter.py`: `kernel.health` patch via registry
- `somatic/signal_bus.py`: `off_any()` for callback removal

### Phase 5 — Tests

- `tests/v04/test_memory_ssot.py`
- `tests/v04/test_retriever_unification.py`
- `tests/v04/test_reversible_wiring.py`

## Follow-up (not in this gate)

- **v02 `IntegrationBus.wire()` / `unwire()`**: still uses ad-hoc `_original_*` fields; migrate to `PatchRegistry` in a follow-up pass
- **v03 `unwire_v03()`**: retains manual restore; migrate to registry when v03 stabilization is touched

## Overall Gate Verdict

**PASS** — All v0.4.1 gate criteria met; `tests/v04/` green.
