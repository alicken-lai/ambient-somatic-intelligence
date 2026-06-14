# Decision Log: DMN Memory Governance Review

Date: 2026-06-09  
Phase: 1G.5 DMN Memory Governance Review  
Status: Accepted as design review artifact. No implementation authorized.

## Decision

Create repository-level DMN memory governance policies for promotion, decay, consolidation, lineage, conflict resolution, and cross-node synchronization.

TurboVec remains paused.

## Findings

- DMN storage is append-only and historically minimal: `content`, `source`, `tags`, and `timestamp`.
- Memory ontology code already defines L1 episodic, L2 instinct, L3 skill, and L4 strategic memory.
- Promotion has the strongest governance support: sequential transitions, confidence thresholds, recurrence requirements, governance approvals, verifier requirements, and audit trails.
- Decay has useful primitives: TTLs, half-lives, inactivity decay, contradiction penalties, failed reuse penalties, archive recommendations, and reporting.
- Consolidation exists locally through pattern mining and attention memory, but not as a DMN-wide replay-preserving lifecycle.
- Lineage exists in trace data and new schemas, but historical DMN records lack universal lineage metadata.
- Conflict detection exists in domain governance modules, but not as one DMN conflict register or workflow.
- Cross-node synchronization remains policy-only and is the least ready area.

## Readiness Score

| Category | Score |
| --- | ---: |
| Promotion | 4 / 5 |
| Decay | 3 / 5 |
| Consolidation | 2 / 5 |
| Lineage | 3 / 5 |
| Conflict Resolution | 2 / 5 |
| Cross-Node Sync | 1 / 5 |

Overall readiness: 17 / 30.

## Risks

- Cross-node synchronization can create ungoverned shared belief if source node, privacy, replay, and conflict metadata are missing.
- Consolidation can erase replayability if source manifests and lineage are not preserved.
- Contradictory memories can be recalled without explanation if conflict state is not attached to recall evidence.
- Historical DMN records need wrappers before embedding, sync, or governance-aware recall.

## Recommended Next Phase

Proceed to a non-production DMN governance examples phase:

1. Create example promoted, decayed, consolidated, conflicted, and synced memory event wrappers.
2. Create a dry-run conflict register format.
3. Create a dry-run cross-node sync manifest format for Home Hermes and Office Hermes.
4. Validate examples against existing schemas or propose schema extensions.

TurboVec should resume only after this governance examples phase passes review.
