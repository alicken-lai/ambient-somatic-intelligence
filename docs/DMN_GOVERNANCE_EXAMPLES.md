# DMN Governance Examples

Phase: 1G.6 DMN Governance Example Wrappers and Sync Manifest Dry Run  
Date: 2026-06-10  
Status: Examples only. No production DMN behavior is changed.

## Purpose

These examples demonstrate how DMN memory can evolve across promotion, decay, consolidation, conflict, and dry-run cross-node synchronization.

All example data is synthetic and non-sensitive. The examples do not mutate `memory/dmn.jsonl`, do not sync real data, do not implement TurboVec, and do not create adapters.

## Created Examples

| File | Demonstrates |
| --- | --- |
| `examples/dmn_governance/promoted_memory.example.json` | A Guardian-reviewed WiFi CSI working-memory event promoted into DMN memory. |
| `examples/dmn_governance/decayed_memory.example.json` | A power fluctuation memory losing active priority without deletion. |
| `examples/dmn_governance/consolidated_memory.example.json` | Temperature and humidity observations consolidated into a higher-level experience while preserving lineage. |
| `examples/dmn_governance/conflicted_memory_a.example.json` | Home Hermes side of an unresolved power/WiFi CSI conflict. |
| `examples/dmn_governance/conflicted_memory_b.example.json` | Office Hermes side of the same unresolved conflict. |
| `examples/dmn_governance/sync_manifest_home_to_office.example.json` | Dry-run sync manifest from Home Hermes to Office Hermes. |

## Wrapper Shape

Each governed memory example uses this structure:

```json
{
  "example_type": "dmn_governance_*",
  "status": "synthetic_non_production",
  "no_mutation": true,
  "memory_event": {},
  "dmn_governance": {}
}
```

The `memory_event` object follows the existing Phase 1B memory event shape where possible. The `dmn_governance` object holds fields not yet present in `schemas/memory_event.schema.json`.

## Validation Results

JSON syntax validation passed for all examples.

Nested `memory_event` objects were validated against `schemas/memory_event.schema.json` for the five memory wrapper examples.

The sync manifest is valid JSON, but no existing schema covers sync manifests yet.

## Schema Amendments Needed Later

Do not modify schemas in this phase. Future schema work should consider:

- A top-level governed memory wrapper schema.
- A DMN governance extension object.
- Promotion fields: `promoted_from`, `promotion_reason`, `promotion_score`, `guardian_review_status`.
- Decay fields: `decay_reason`, `half_life`, `last_reused_at`, `current_importance_score`.
- Consolidation fields: `consolidated_from`, `source_record_count`, `pattern_summary`, `representative_examples`.
- Conflict fields: `conflict_group_id`, `conflict_type`, `competing_claim`, `requires_review`.
- Sync manifest fields: allowed records, excluded records, filters, conflict candidates, replay references, and `no_mutation`.

## Updated Readiness

Phase 1G.5 readiness was 17 / 30.

These examples improve practical demonstrability but do not implement missing governance machinery. Updated readiness: 20 / 30.

Remaining blockers are sync schema, conflict register schema, implementation gates, and validation for real historical DMN wrappers.

TurboVec remains paused.
