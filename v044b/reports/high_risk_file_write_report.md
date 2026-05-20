# High-Risk File Write Migration (v0.4.4B Phase 1)

**Generated:** 2026-05-18

## Migrated modules

| Module | Guard | Notes |
|--------|-------|-------|
| `governance/audit_log.py` | `GuardedFileWriter` + `AuthorityTrace` | Opt-in via `execution_context` |
| `memory/memory_kernel.py` | `GovernedMemoryWriter` | `store()` governed path |
| `kernel/isolation/governed_memory_writer.py` | New SSOT for DMN/layer writes | Legacy fallback without context |
| `runtime/task_graph/checkpoint.py` | `GuardedFileWriter` | `save(execution_context=...)` |
| `runtime/isolation_kernel/execution_sandbox.py` | `GovernanceAuditLog` delegation | Sandbox audit persistence |
| `runtime/evolution_engine/patch_proposer.py` | `GovernanceAuditLog` trace | Proposal audit only |

## Out of scope (unchanged per constitution)

- `memory/ontology/*` promotion paths — ontology/promotion not modified
- Guardian, verifier, telemetry scoring

## Backward compatibility

Legacy callers without `ExecutionContext` continue using direct `open`/`append` paths.
