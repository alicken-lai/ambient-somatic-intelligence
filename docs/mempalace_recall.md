# MemPalace Recall

`scripts/query_mem_palace.py` is the read-only CLI for querying `tools/mempalace/palace.json`.

## Queries

- `summary`: returns node and link counts plus per-domain counts.
- `domain`: returns nodes in a single domain.
- `anomaly_type`: returns nodes matching an anomaly type.
- `confidence`: returns nodes sorted by confidence.
- `linked_events`: returns nodes with linked events.
- `lessons`: returns the lessons attached to recalled nodes.

## Examples

```bash
python3 scripts/action_router.py mem-palace-query summary
python3 scripts/action_router.py mem-palace-query domain --domain memory_pressure
python3 scripts/action_router.py mem-palace-query confidence --json
python3 scripts/action_router.py mem-palace-query lessons
```

## Notes

- The command is routed through Guardian as `OBSERVE_ONLY`.
- The CLI only reads `tools/mempalace/palace.json`.
- Query actions are logged append-only.
