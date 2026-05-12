# Night 37 Hermes Gateway Recovery

Mission: Hermes Gateway Safe Recovery
Timestamp: 2026-05-13 07:17 Asia/Taipei

## Guardrails

- Guardian allowed the narrowed local recovery action.
- No credential values were changed.
- No credential files were removed.
- No reinstall was performed.
- No external actions or CUA were enabled.
- The Ambient DMN tick loop was not modified.
- The Hermes MCP shim was left intact.

## Injection Path

The LaunchAgent at:

`/Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist`

does not inject `DISCORD_BOT_TOKEN` directly. Its environment contains
`HERMES_HOME=/Users/alicken/.hermes`, `PATH`, and `VIRTUAL_ENV`.

Hermes loads `/Users/alicken/.hermes/.env` during `hermes_cli.main` import via:

```text
hermes_cli.main -> hermes_cli.env_loader.load_hermes_dotenv()
```

`gateway.config._apply_env_overrides()` then sees `DISCORD_BOT_TOKEN` and
auto-enables Discord:

```text
discord_token = os.getenv("DISCORD_BOT_TOKEN")
if discord_token:
    config.platforms[Platform.DISCORD].enabled = True
```

Because `discord.py` is absent from the Hermes runtime, the adapter cannot be
created and the gateway exits when Discord is the only auto-enabled platform.

## Isolation Options Considered

1. Remove token only from LaunchAgent environment.
   Not sufficient: the token is not present in the LaunchAgent environment; it
   is loaded later from `HERMES_HOME/.env`.

2. Set an explicit adapter allowlist.
   No supported adapter allowlist or config key was found that wins after
   `_apply_env_overrides()`.

3. Override the Hermes gateway runtime to exclude Discord.
   Chosen. A small gateway-only wrapper lets Hermes load its normal environment,
   removes `DISCORD_BOT_TOKEN` from the process environment only, and then runs
   the normal gateway command. The credential file remains unchanged.

## Applied Minimal Change

Added:

`scripts/hermes_gateway_no_discord.py`

The wrapper:

- Adds the Hermes runtime site-packages path.
- Wraps `hermes_cli.env_loader.load_hermes_dotenv()`.
- Lets Hermes load the normal `.env`.
- Removes `DISCORD_BOT_TOKEN` from the current process environment only.
- Calls `hermes gateway run --replace` through `hermes_cli.main`.

Updated LaunchAgent `ProgramArguments` to:

```text
/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python
/Users/alicken/ambient-os/scripts/hermes_gateway_no_discord.py
```

No token value was edited. `/Users/alicken/.hermes/.env` was not modified.

## Restart

Restart sequence:

```text
launchctl bootout gui/501 /Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist
launchctl bootstrap gui/501 /Users/alicken/Library/LaunchAgents/ai.hermes.gateway.plist
```

The first non-escalated bootstrap attempt was denied by launchd policy. The
approved retry succeeded.

## Verification

`launchctl print gui/501/ai.hermes.gateway` after restart:

- State: `running`
- Runs: `1`
- PID: `57307`
- Last exit code: `(never exited)`
- Program: `/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/bin/python`
- Argument: `/Users/alicken/ambient-os/scripts/hermes_gateway_no_discord.py`

Gateway log after restart:

```text
No messaging platforms enabled.
Gateway will continue running for cron job execution.
Channel directory built: 0 target(s)
Cron ticker started (interval=60s)
```

This confirms the repeated exit code 1 loop stopped without enabling Discord or
any other external messaging adapter.

One nonfatal follow-on log appeared from the embedded kanban dispatcher:

```text
sqlite3.OperationalError: database is locked
```

The gateway remained running after that error, so it is not the original
LaunchAgent failure mode.

## DMN Tick Health

`launchctl print gui/501/ai.ambient-os.dmn-tick`:

- State: `running`
- PID: `53183`
- Runs: `2`
- Program: `/opt/homebrew/bin/python3 -B /Users/alicken/ambient-os/scripts/dmn_tick_loop.py --interval 60`

## MCP Memory Recall

Hermes MCP `memory_recall` for `Night 36 Hermes gateway diagnosis` returned a
high-confidence match:

```text
logs/night36_hermes_gateway_diagnosis.md:1
confidence: 0.95
null_recall: false
```

## MCP Shim Integrity

The repo-managed shim and installed Hermes shim still match:

```text
diff -u tools/hermes_mcp_shim/mcp_serve.py /Users/alicken/.hermes/mcp_shim/mcp_serve.py
```

The diff produced no output.

## Result

`ai.hermes.gateway` recovered safely. Discord auto-enable is isolated from the
gateway process without credential deletion, token mutation, reinstall, CUA, or
external adapter enablement.
