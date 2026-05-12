# Night 36 Hermes Gateway Diagnosis

Mission: Hermes Gateway Recovery
Route: local read-only diagnosis first
Timestamp: 2026-05-13 07:12 Asia/Taipei

## Guardrails

- Guardian classified the work as `OBSERVE_ONLY` and allowed it.
- No reinstall was performed.
- No credentials or allowlists were mutated.
- No LaunchAgent plist was edited.
- No Ambient DMN tick loop code or LaunchAgent was modified.
- No external actions or CUA were enabled.

## LaunchAgent

LaunchAgent path:

`/Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist`

`launchctl print gui/501/ai.hermes.gateway` reported:

- State: `spawn scheduled`
- Runs: `999`
- Last exit code: `1`
- Program: `/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python`
- Working directory: `/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/lib/python3.14/site-packages`
- Stdout: `/Users/alicken/.hermes/logs/gateway.log`
- Stderr: `/Users/alicken/.hermes/logs/gateway.error.log`

## ProgramArguments

The plist `ProgramArguments` are:

```text
/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python
-m
hermes_cli.main
gateway
run
--replace
```

The command path exists and is a symlink:

```text
/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python -> python3.14
```

The configured working directory exists and contains the Hermes runtime package,
including `hermes_cli`, `gateway`, and `hermes_agent-0.13.0.dist-info`.

## Launchd Logs

Unified launchd logs over the inspected 30 minute window repeatedly report:

```text
service inactive: ai.hermes.gateway
```

The cadence is roughly every 10 seconds, matching the LaunchAgent repeatedly
starting and exiting rather than failing to spawn.

## Hermes Logs

Recent Hermes stdout shows each run reaches the gateway process:

```text
Starting Hermes Gateway...
Session storage: /Users/alicken/.hermes/sessions
Secret redaction: ENABLED
```

Recent Hermes stderr repeats:

```text
No user allowlists configured. All unauthorized users will be denied.
Discord: discord.py not installed
No adapter available for discord
Gateway failed to connect any configured messaging platform: all configured messaging platforms failed to connect
```

## Configuration Evidence

`/Users/alicken/.hermes/config.yaml` has top-level platform sections for
Discord, Telegram, Slack, and other platforms, but no explicit
`display.platforms` entries.

Secret values were not printed. The only gateway-impacting environment key
observed in `/Users/alicken/.hermes/.env` was:

```text
DISCORD_BOT_TOKEN
```

Hermes gateway config code auto-enables Discord when `DISCORD_BOT_TOKEN` is set.
The active Hermes Python environment reports:

```text
discord_spec None
```

So launchd starts Hermes successfully, Hermes auto-enables Discord from the
environment, and adapter construction fails because `discord.py` is absent.

## MCP Shim Comparison

Repo-managed shim:

`tools/hermes_mcp_shim/mcp_serve.py`

Installed Hermes shim:

`/Users/alicken/.hermes/mcp_shim/mcp_serve.py`

`diff -u` produced no output, so the two files are identical at inspection time.

The live process table also showed Codex MCP processes running:

```text
/opt/homebrew/bin/hermes mcp serve
```

This confirms the gateway crash is not explained by a repo-managed MCP shim
path mismatch.

## DMN Tick Health

The Ambient DMN tick LaunchAgent remains healthy:

- Label: `ai.ambient-os.dmn-tick`
- State: `running`
- PID: `53183`
- Program: `/opt/homebrew/bin/python3 -B /Users/alicken/ambient-os/scripts/dmn_tick_loop.py --interval 60`
- Runs: `2`

The live process table showed the same DMN tick loop process alive, started
Tue May 12 22:04:16 2026.

The current system state still reports:

- Health score: `76.53`
- Health risk: `watch`
- DMN append count: `172`
- Corrective actions: `none`

## Likely Root Cause

Most likely root cause:

`DISCORD_BOT_TOKEN` is present in Hermes environment, which auto-enables the
Discord platform, but the Hermes runtime does not have `discord.py` installed.
Because Discord is the only configured messaging platform with an enabling
environment key, the gateway has zero usable adapters and exits with code 1.

This is not a ProgramArguments failure, not a missing command path, not a
missing working directory, and not an MCP shim mismatch.

## Safe One-Line Fix Candidate

Do not apply automatically under the Night 36 constraints.

If Discord is the intended gateway platform, the likely one-line recovery is:

```text
/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python -m pip install discord.py
```

If Discord is not intended, the recovery path is to remove or disable the
Discord-enabling environment setting, but that would mutate credentials and was
therefore not performed or recommended as an automatic fix.

