# Night 34 Memory Recall Smoke Test

Route: memory-recall-build
Generated: 2026-05-12
Mode: recommendations only.

## Queries

### `memory_recall("Night 0")`

- Null recall: false.
- Match count: 17.
- Overall confidence: 0.9983.
- Latency: 23.35 ms.
- Top provenance:
  - `memory/dmn.jsonl:2` (`dmn`), confidence 0.9983, `Night 0 bootstrap initialized`.
  - `logs/night0.log:1` (`night_log`), confidence 0.95.

### `memory_recall("Guardian")`

- Null recall: false.
- Match count: 297.
- Overall confidence: 0.9997.
- Latency: 20.72 ms.
- Top provenance:
  - `state/system_state.json:palace_nodes.guardian_reflex` (`system_state`), confidence 0.9997.
  - `memory/dmn.jsonl:81` (`dmn`), confidence 0.9997.
  - `tools/mempalace/palace.json:queue:guardian/incidents/incident-2026-05-11T214902.702883Z0000.md` (`mempalace`), confidence 0.9997.

### `memory_recall("Genesis")`

- Null recall: false.
- Match count: 3.
- Overall confidence: 0.95.
- Latency: 20.43 ms.
- Top provenance:
  - `logs/actions.jsonl:348` (`night_log`), confidence 0.95.
  - `logs/checksums.jsonl:545` (`night_log`), confidence 0.95.
  - `memory/dmn.jsonl:88` (`dmn`), confidence 0.8797.

### `memory_recall("Nonexistent memory")`

- Null recall: true.
- Match count: 0.
- Overall confidence: 0.0.
- Latency: 20.46 ms.
- Behavior: no inferred or fabricated result returned.

## Latency

- Minimum: 20.43 ms.
- Average: 21.24 ms.
- Maximum: 23.35 ms.

## Confidence Distribution

- Exact band (`0.90-1.00`): 313 matches.
- Tag band (`0.70-0.89`): 3 matches.
- Semantic band (`0.40-0.69`): 1 match.
- Weak contextual band (`0.20-0.39`): 0 matches.
- Null (`0.00`): 1 query.

## Verification

- Ranked results: pass.
- Provenance fields: pass.
- Confidence fields: pass.
- Null recall: pass.

## Retrieval Gaps

- `Guardian` returns a broad result set because it is present across DMN tags, MemPalace node identifiers, log text, and system_state paths.
- `Genesis` has stronger log provenance than DMN provenance because the DMN match is tag-based while log entries contain the exact phrase.
- `system_state` still reflects the Phase 1 DMN count mismatch and should not be treated as the authoritative DMN record total until refreshed in a separate route.
