# DMN Conflict Register Dry Run

Phase: 1G.6 DMN Governance Example Wrappers and Sync Manifest Dry Run  
Date: 2026-06-10  
Status: Dry run only. No conflict register is implemented.

## Purpose

This document demonstrates how two contradictory synthetic memories can coexist without automatic resolution.

The example conflict group is:

`conflict-power-wifi-csi-2026-06-10-001`

## Conflict Pair

| File | Source Node | Claim | Confidence |
| --- | --- | --- | ---: |
| `examples/dmn_governance/conflicted_memory_a.example.json` | Home Hermes | A power fluctuation occurred during the WiFi CSI anomaly window. | 0.73 |
| `examples/dmn_governance/conflicted_memory_b.example.json` | Office Hermes | No power fluctuation occurred during the compared WiFi CSI anomaly window. | 0.69 |

## Register Entry Shape

A future conflict register could store:

```json
{
  "conflict_group_id": "conflict-power-wifi-csi-2026-06-10-001",
  "conflict_type": "source_conflict",
  "record_ids": [
    "mem_1.0.0_home-hermes_system_power-conflict-a-d4e5f6g7",
    "mem_1.0.0_office-hermes_system_power-conflict-b-e5f6g7h8"
  ],
  "resolution_state": "unresolved",
  "requires_review": true,
  "auto_resolution_allowed": false
}
```

This is illustrative only. No schema or runtime conflict register is created in this phase.

## Governance Rule Demonstrated

The examples show:

- newer is not automatically correct;
- higher confidence is not automatically decisive;
- source-node identity must be preserved;
- unresolved conflicts block sync and promotion;
- recall should expose conflict state;
- human or Guardian review is required before governance use.

## Remaining Gap

The repository still needs a formal conflict register schema and validation examples before cross-node sync or vector recall can rely on conflict metadata.
