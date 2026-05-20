# Constitutional Boundary Inventory (v0.6.1)

| Boundary | Module | Violation action |
|----------|--------|------------------|
| Guardian supremacy | `guardian_supremacy.py` | Block before arbitration |
| Epistemic limit | `epistemic_limit.py` | Block certainty / deterministic authority |
| Replay boundary | `replay_boundary.py` | Block replay execution / excessive hint |
| Forecast boundary | `forecast_boundary.py` | Block uncertainty collapse |
| Self-modification | `self_modification_guard.py` | Block runtime rule mutation |
| Constitutional lock | `constitutional_lock.py` | Seal rules at load |
| Recursive governance | `constitutional_guard.py` | Block forbidden routes |

## Out of scope (unchanged)

- Ontology, TruthGraph, Entropy, Isolation, PatchRegistry
- Guardian policy engine (separate execution gate)
- Dynamic constitutional mutation (forbidden)
