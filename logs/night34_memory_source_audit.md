# Night 34 Memory Source Audit

Route: memory-recall-build
Generated: 2026-05-12
Mode: recommendations only; no source repairs performed.

## Sources Inspected

- DMN: `memory/dmn.jsonl`
- Night logs: `logs/`
- MemPalace: `tools/mempalace/palace.json`
- system_state: `state/system_state.json`

## DMN

- File exists and is readable.
- JSONL validity: pass.
- Schema consistency: pass. All 87 records use `content`, `source`, `tags`, `timestamp`.
- Append-only consistency: pass by observed timestamp order and duplicate-record scan.
- Duplicate records: 0.
- Checksum chain: pass (`checksum chain valid`).

## Night Logs

- Directory exists and is readable.
- JSONL files:
  - `logs/actions.jsonl`: 357 valid records.
  - `logs/checksums.jsonl`: 557 valid records.
- Text/Markdown/log files are readable:
  - `logs/github_release_audit.md`
  - `logs/hermes_install.md`
  - `logs/hermes_mcp_memory_tools.md`
  - `logs/hermes_mcp_shim.md`
  - `logs/night0.log`
  - `logs/night1_substrate.md`
  - `logs/system_audit.md`
- JSON validity: pass for JSONL log sources.
- Append-only consistency: no mutation performed; checksum chain passed.

## MemPalace

- File exists and is readable.
- JSON validity: pass.
- Schema consistency: pass for observed palace node shape.
- Declared node count: 8.
- Actual node count: 8.
- Declared link count: 4.
- Actual link count: 4.
- Node fields present across all nodes: `anomaly_type`, `confidence`, `domain`, `event_id`, `explanation`, `lessons`, `linked_events`, `timestamp`.

## system_state

- File exists and is readable.
- JSON validity: pass.
- Schema consistency: pass for required operational keys inspected.
- Generated at: `2026-05-12T09:11:29.911918+00:00`.
- Authoritative sources listed: 16.

## Mismatches

- `state/system_state.json` reports `dmn_append_count=83`, while `memory/dmn.jsonl` currently contains 87 valid non-empty records.

## Recommendations

- Do not repair during Night 34.
- Treat the `dmn_append_count` mismatch as a stale derived-state gap.
- Rebuild `state/system_state.json` in a separate state-refresh route before using DMN counts as authoritative operational totals.
