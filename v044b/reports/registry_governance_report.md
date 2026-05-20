# Registry Governance (v0.4.4B Phase 2)

## Integrated registries

| Registry | Guard binding | AuthorityTrace |
|----------|---------------|----------------|
| `PatchRegistry` | `patch_registry` → `INTEGRATION_BUS` | via `RegistryGuard` |
| `TruthRegistry` | `truth_registry` → `TRUTH_GRAPH` | via `RegistryGuard` |
| `EventSchemaRegistry` | `event_schema_registry` → `INTEGRATION_BUS` | `register_schema()` |
| `SkillRegistry` | `skill_registry` → `SKILL_REGISTRY` | (v0.4.4 baseline) |

## Behavior

- `execution_context` provided → `RegistryGuard.mutate()` + trace emission
- Anonymous mutation when guard inactive → auto ephemeral context (v0.4.4 compat)
- `require_context=True` on guard blocks anonymous writes (opt-in strict mode)
