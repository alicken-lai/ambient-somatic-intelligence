# Hermes MCP Shim

This directory keeps the Hermes MCP shim reproducible inside the Ambient OS
repository. The shim exposes Hermes messaging tools plus Ambient OS memory,
Guardian, system state, and log query tools over MCP.

## Files

- `mcp_serve.py`: repo-managed MCP server shim.
- `codex_mcp_config.example.toml`: example Codex MCP registration.
- `install.sh`: optional helper that copies the shim into a Hermes runtime home.

## Requirements

- Python 3.10+
- Hermes runtime modules available on `PYTHONPATH`
- `mcp` Python package available to the Hermes MCP server process
- Ambient OS checkout available through `AMBIENT_OS_ROOT`

Install the MCP SDK into the same Python environment used by Hermes when needed:

```sh
python3 -m pip install mcp
```

## Installation

From the repository root:

```sh
tools/hermes_mcp_shim/install.sh
```

By default, the installer copies `mcp_serve.py` to:

```text
${HERMES_HOME:-$HOME/.hermes}/mcp_shim/mcp_serve.py
```

To install into an explicit runtime home:

```sh
HERMES_HOME=/path/to/hermes-home tools/hermes_mcp_shim/install.sh
```

The installer only copies the shim file. It does not write secrets or modify
client configuration.

## Codex MCP Registration

Use `codex_mcp_config.example.toml` as a starting point. The key details are:

- `command` should invoke the Hermes CLI.
- `args` should start the MCP server with `mcp serve`.
- `PYTHONPATH` should include the installed shim directory and any Hermes
  dependency directory required by the local Hermes runtime.
- `AMBIENT_OS_ROOT` should point at this repository checkout.
- `HERMES_HOME` should point at the Hermes runtime home.

The example uses placeholder paths. Replace them for the target machine.

## Exposed Ambient OS Tools

### `dmn_search`

Searches append-only DMN memory records.

Arguments:

- `query`: case-insensitive text to find in memory records.
- `limit`: maximum number of matching records to return.

### `dmn_append`

Appends a record to DMN memory through the existing `remember.py` helper.

Arguments:

- `content`: memory content to append.
- `tags`: optional list of tags.
- `source`: source label for the memory record; defaults to `hermes-mcp`.

### `mempalace_query`

Queries MemPalace through `query_mem_palace.py`, or performs a simple free-text
search over the palace JSON for non-native query strings.

Arguments:

- `query`: one of `summary`, `domain`, `anomaly_type`, `confidence`,
  `linked_events`, `lessons`, or arbitrary free text.
- `domain`: optional MemPalace domain filter.
- `anomaly_type`: optional anomaly type filter.

### `guardian_check`

Classifies an action against Ambient OS Guardian policy.

Arguments:

- `action`: action or command description to classify.
- `route_name`: optional decision-boundary route name.

### `system_state_read`

Reads Ambient OS system state through `query_state.py`.

Arguments:

- `query`: one of `summary`, `health`, `incidents`, `memory`, `reflex`,
  `dashboard`, or `digest`.

### `night_log_search`

Searches Ambient OS Night logs and markdown/JSONL logs.

Arguments:

- `query`: case-insensitive text to find in log files.
- `limit`: maximum number of matching lines to return.

## Verification

After installation, restart the MCP client and list the tools for the `hermes`
server. The Ambient OS tool list should include:

```text
dmn_search
dmn_append
mempalace_query
guardian_check
system_state_read
night_log_search
```

