# Hermes MCP Memory Tools

Timestamp: 2026-05-12T13:22:00Z

## Goal

Hermes MCP was reachable from Codex, but only conversation, channel, event, messaging, and approval tools were exposed. Codex needed MCP-callable memory and state tools for Ambient OS.

## Configuration Inspected

- Codex MCP config: `/Users/alicken/.codex/config.toml`
- Hermes MCP shim: `/Users/alicken/.hermes/mcp_shim/mcp_serve.py`
- Hermes runtime config: `/Users/alicken/.hermes/config.yaml`
- Hermes gateway LaunchAgent: `/Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist`
- Ambient OS data sources:
  - `memory/dmn.jsonl`
  - `tools/mempalace/palace.json`
  - `guardian/policy.yaml`
  - `guardian/decision_boundary.yaml`
  - `state/system_state.json`
  - `logs/`

## MCP Tools Before

Fresh MCP list-tools smoke test before the wrapper change exposed 10 tools:

- `conversations_list`
- `conversation_get`
- `messages_read`
- `attachments_fetch`
- `events_poll`
- `events_wait`
- `messages_send`
- `channels_list`
- `permissions_list_open`
- `permissions_respond`

## Finding

The Hermes MCP shim identifies itself as a messaging bridge and only registers the tools above. No native MCP tools for DMN memory, MemPalace, Guardian policy, system state, or Night logs were present in the inspected shim.

The underlying Ambient OS capabilities already exist as local files and scripts. The missing layer was MCP exposure, not memory storage.

## Change Made

Added local MCP wrapper tools to `/Users/alicken/.hermes/mcp_shim/mcp_serve.py` without changing the existing messaging tools:

- `dmn_search`
- `dmn_append`
- `mempalace_query`
- `guardian_check`
- `system_state_read`
- `night_log_search`

The wrappers use `AMBIENT_OS_ROOT` when set, defaulting to `/Users/alicken/ambient-os`.

## MCP Tools After

Fresh MCP list-tools smoke test after the wrapper change exposed 16 tools:

- `conversations_list`
- `conversation_get`
- `messages_read`
- `attachments_fetch`
- `events_poll`
- `events_wait`
- `messages_send`
- `channels_list`
- `permissions_list_open`
- `permissions_respond`
- `dmn_search`
- `dmn_append`
- `mempalace_query`
- `guardian_check`
- `system_state_read`
- `night_log_search`

## Memory Recall Test

Question:

```text
What memories exist about Ambient Somatic Intelligence Night 0?
```

MCP test calls:

- `dmn_search(query="Night 0", limit=10)`
- `night_log_search(query="Ambient Somatic Intelligence Night 0", limit=10)`
- `mempalace_query(query="Ambient Somatic Intelligence Night 0")`
- `system_state_read(query="memory")`

Result:

- DMN returned one memory: `Night 0 bootstrap initialized`, source `bootstrap`, tag `night0`, timestamp `2026-05-11T12:54:11.088554+00:00`.
- Night log search returned one line from `logs/night0.log`: `AMBIENT SOMATIC INTELLIGENCE Night 0 Smoke Test`.
- MemPalace free-text search returned no exact match for `Ambient Somatic Intelligence Night 0`.
- System state read confirmed DMN memory source and reported `dmn_append_count: 83` from `state/system_state.json`.

## Null Recall Signal

MemPalace currently does not support exact free-text recall for `Ambient Somatic Intelligence Night 0`.

This is recorded as:

- Limitation: MemPalace does not return an exact phrase match for this Night 0 query.
- Future improvement: add a unified memory recall surface that can search across heterogeneous memory stores.
- Indexing/query-normalization gap: MemPalace needs normalized aliases such as `Night 0`, `night0`, `Ambient Somatic Intelligence Night 0`, and related milestone labels.

Null recall is a valid signal and should remain visible in test results. Do not hide empty result sets from MemPalace or any other memory source.

## Recommendation

Create a unified memory recall tool that queries:

1. DMN
2. Night logs
3. MemPalace
4. `system_state`

The tool should return ranked results with provenance, including source file, source system, matched field or line, timestamp when available, score, and whether the result was exact, normalized, semantic, or null.

## Remaining Limitations

- The current Codex session does not hot-reload MCP tool namespaces. A new Codex session is required before the new `mcp__hermes__` tools appear directly in the tool palette.
- The live Hermes MCP shim is under `/Users/alicken/.hermes`, outside the `ambient-os` git worktree.
- MemPalace currently does not contain an exact free-text node for the full phrase `Ambient Somatic Intelligence Night 0`; the Night 0 evidence is in DMN memory and `logs/night0.log`. This is an indexing/query-normalization gap, not evidence that the event did not occur.
- Codex config currently points at `hermes mcp serve` with `PYTHONPATH=/Users/alicken/.hermes/mcp_shim:/Users/alicken/.hermes/mcp_deps`, so the wrapper registration depends on that shim path remaining in place.
