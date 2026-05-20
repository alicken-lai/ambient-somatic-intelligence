# Clean Graph Definition (v0.4.5)

A **clean graph** is the minimal stability fixture used by gate tests and boot baselines.

## Truth graph

| Property | Requirement |
|----------|-------------|
| Nodes | ≥ 1 registered baseline node |
| Duplicates | 0 duplicate-version conflicts |
| Checksum | 0 checksum divergence |
| Cycles | 0 circular version dependencies |
| Orphans | 0 orphan nodes **when edges exist**; edgeless single-root graphs are not orphans |
| Stale truth | 0 stale truth sources |

## Entropy / patch

| Property | Requirement |
|----------|-------------|
| Patch leakage | 0 inactive-but-registered patches |
| Patch restore | `unwire_success_ratio` = 1.0 |
| Circular coupling | 0 critical circular recursion |
| Module orphan pressure | 0 (no module inventory in fixture) |
| Mutation pressure | 0 recorded denials in fixture window |

## State / runtime

| Property | Requirement |
|----------|-------------|
| Stale critical | 0 critical stale sources |
| Fresh artifacts | `system_state.json` and `dmn.jsonl` timestamps within warning window |
| Runtime reproducibility | Derived from patch + mutation pressures; must not penalize clean evidence |

## Stability gate

- Composite **stability score ≥ 0.85**
- Critical evidence: `duplicate_truth_count=0`, `patch_leakage=0`, `circular_recursion=0`, `stale_state_critical=0`
- **Semantics alignment ≥ 0.95** — dimensions must not contradict clean critical evidence

## Non-goals

- Production module inventory scans (orphan classification across repo) are not part of the clean-graph fixture.
- Operational patch churn/age metrics do not fail the gate when leakage and restore health are zero.
