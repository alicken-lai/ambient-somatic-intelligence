# Hermes-ASI Provider Orchestration

Hermes is an orchestration layer for exposed providers, not a direct controller for IDE internals.

**IDEs are not providers. Exposed agents, CLI bridges, MCP servers, or OpenAI-compatible endpoints are providers.**

## Architecture

```text
User / Telegram
-> Hermes-ASI Router
-> Provider Registry
-> Routing Rules
-> Provider Adapter
-> Model / IDE Worker / CLI Agent
-> Result returned to Hermes
```

## Files

- `config/provider_registry.yaml` declares provider endpoints, models, capabilities, priority, cost, latency, health checks, and fallback providers.
- `config/routing_rules.yaml` maps task categories to provider preference and governance defaults.
- `hermes/orchestration/models.py` defines provider, routing, request, policy, and normalized response models.
- `hermes/orchestration/adapters.py` defines `ProviderAdapter` and the OpenAI-compatible adapter.
- `hermes/orchestration/guardian.py` defines the Guardian enforcement seam.
- `hermes/orchestration/audit.py` defines no-op, memory, and JSONL audit sinks.
- `hermes/orchestration/health.py` coordinates health checks.
- `hermes/orchestration/routing.py` selects providers, applies governance policy, and handles fallback.
- `scripts/hermes.py` exposes the `hermes route` CLI behavior.

## Provider Registry

Example provider config:

```yaml
cursor_worker:
  enabled: true
  type: openai-compatible
  base_url: http://localhost:8781/v1
  api_key_env: CURSOR_WORKER_API_KEY
  default_model: cursor/active
  available_models:
    - cursor/active
  capabilities:
    - repo_edit
    - codebase_context
    - refactor
    - diff_generation
    - local_file_access
  priority: 10
  cost_tier: medium
  latency_tier: low
  context_window: 128000
  health_check_endpoint: /health
  fallback_provider: vscode_worker
  allow_cloud: false
```

Provider types currently modeled:

- `copilot`
- `openai-compatible`
- `openrouter`
- `local-cli`
- `mcp-agent`
- `hermes-subagent`

These types identify adapter behavior and governance expectations. They do not imply Hermes can consume a private IDE quota unless that IDE exposes a supported bridge.

## IDE Worker Bridge Contract

Cursor, VS Code, Claude Desktop, Grok App, and Antigravity are not treated as providers by themselves. A worker bridge must expose:

```text
POST /v1/chat/completions
GET /health
GET /v1/models
```

The bridge should declare:

- `ide_name`
- `session_id`
- `workspace_path`
- `capabilities`
- `active_model`
- `availability`
- `max_context`
- `permissions`

Example capabilities:

```yaml
cursor_worker:
  - repo_edit
  - codebase_context
  - refactor
  - diff_generation

vscode_worker:
  - filesystem
  - terminal
  - test_runner
  - local_debug

claude_desktop_worker:
  - long_reasoning
  - writing
  - architecture_review
  - mcp_tools
```

## Governance Policy

Per-request policy fields:

- `allow_cloud`
- `allow_local_file_access`
- `allow_code_modification`
- `allow_terminal_execution`
- `allow_mcp_tools`
- `max_cost_tier`
- `preferred_provider`
- `require_preferred_provider`
- `no_fallback`

Routing rule boolean fields (`allow_cloud`, `allow_local_file_access`, `allow_code_modification`, and
`allow_terminal_execution`) must be actual YAML booleans (`true` / `false`) or omitted / `null`.
Quoted strings such as `"false"` and `"true"` are rejected because they can otherwise become truthy
and change policy semantics.

Hermes must not:

- secretly access IDE internal quotas
- assume client quota is available
- route private repo content to cloud providers unless allowed
- use expensive models for cheap batch tasks unless explicitly requested
- perform destructive local file operations without permission

## Routing Strategy

- Local repo editing prefers IDE worker or Codex CLI worker.
- Deep architecture reasoning prefers strongest Copilot or OpenRouter reasoning models.
- Fast answers prefer active Copilot or fast OpenRouter/local models.
- Cheap batch prefers Qwen, DeepSeek, or local models.
- Sensitive local memory prefers local providers or explicit user-approved cloud routes.

Example command:

```bash
python scripts/hermes.py route --task code_edit --prompt "Refactor this repo module"
```

Dry-run example result:

```text
Selected provider: cursor_worker
Fallback: copilot
Reason: task requires repo_edit capability
```

To actually invoke a provider bridge, pass `--invoke`. The default is dry-run to avoid accidental external calls.

Dry-run output includes `dry_run: true`, `health_checked: false`, and a log entry stating that provider availability was not verified. Use `--check-health` with dry-run to validate bridge availability without invoking `/v1/chat/completions`.

Live invocation uses real health checks before `POST /v1/chat/completions` and returns a structured error if no eligible healthy provider is available. Do not claim end-to-end cross-IDE invocation works unless `--invoke` succeeds against a real worker bridge.

## Permission Composition

Request / user / Guardian policy is the authority for grants. Routing rules can narrow permissions and express route constraints, but they cannot silently enable local file access, code modification, terminal execution, or cloud routing. Effective policy is computed as the request policy combined with rule constraints, with the stricter value winning.

Relationship, role, trust labels, Father/Mother framing, routing rules, task type, and "trusted user" semantics are not authorization. Love, context, and relationship are not credentials. Dangerous actions require request policy permission and Guardian approval.

Dangerous capabilities include:

- `local_file_access`
- `repo_edit`
- `terminal`
- `filesystem`
- `test_runner`
- `local_sensitive`
- `mcp_tools`

Dangerousness is computed from the effective requested route capabilities: request-required capabilities, routing-rule required capabilities, and capabilities inferred from exposed tools. A provider is not treated as dangerous merely because it advertises dangerous capabilities that are not requested for the current route. If a task type semantically needs dangerous access, encode that in the routing rule required capabilities.

`test_runner` always requires execution permission through `allow_terminal_execution`, even if the selected provider advertises `test_runner` but not `terminal`. `mcp_tools` always requires request-level `allow_mcp_tools`. These flags are necessary but not sufficient: dangerous live invocation still requires Guardian `ALLOW`.

Routing config lint includes deterministic task-safety checks for semantically dangerous task names. Rules named like `code_edit`, `edit`, `write`, `patch`, `refactor`, or `modify` should declare `repo_edit` and `local_file_access` or `filesystem`. Rules named like `test_runner`, `test`, or `run_tests` should declare `test_runner` or `terminal`. Rules named like `shell`, `terminal`, `command`, `exec`, or `run_command` should declare `terminal`. Sensitive memory, secret, and credential tasks should declare `local_sensitive` or local file capability. Browser/network/http/fetch/url/send_message/mcp tasks should declare `mcp_tools`. The lint is a warning/issue helper; dangerous behavior still depends on effective requested capabilities and Guardian.

For live invocation, dangerous routes must receive explicit Guardian `ALLOW` before provider invocation. `BLOCK` returns a structured `guardian_block` error. `REVIEW_REQUIRED` returns a structured `guardian_review_required` error and does not auto-proceed. `NOT_CHECKED` returns a structured `guardian_not_checked` error, and any other non-`ALLOW` decision returns `guardian_not_allowed`. If no real Guardian integration is configured for invoke mode, routing fails closed for dangerous routes.

Dry-run is planning only. Dangerous dry-runs without an injected Guardian are marked with `guardian_checked: false` and `guardian_decision: NOT_CHECKED`; this is not approval to invoke.

Tool definitions should declare explicit Hermes capability metadata when possible:

```json
{
  "type": "function",
  "function": {
    "name": "writeText",
    "x-hermes-capabilities": ["repo_edit", "local_file_access"]
  }
}
```

Supported metadata locations are `tool.capabilities`, `tool["x-hermes-capabilities"]`, `tool.function["x-hermes-capabilities"]`, and `tool.metadata.capabilities`. Unknown explicit capabilities are rejected with a structured route error. Explicit metadata is preferred over heuristic inference because tool names are not a security boundary.

Explicit tool metadata may only declare tool exposure capabilities: `terminal`, `filesystem`, `local_file_access`, `repo_edit`, `mcp_tools`, `test_runner`, and `local_sensitive`. Broader provider/task capabilities such as `general_reasoning` and `creative_generation` are rejected in tool manifests with `invalid_tool_capability`; route-level required capabilities remain broader.

Explicit metadata is unioned with conservative heuristic inference. Under-declaration cannot reduce inferred risk: a tool named `terminal_exec` still implies `terminal`, and a tool named `writeFile` still implies `repo_edit`, `filesystem`, and `local_file_access`, even if the manifest only declares a narrower exposure. Tokenization splits snake_case, kebab-case, dotted namespaces, slash paths, and camelCase/PascalCase. Markers include terminal execution terms such as `run`, `execute`, `bash`, `powershell`, `pwsh`, `python`, `node`, `npm`, and `npx`; file terms such as `readFile`, `writeFile`, `writeText`, `fs`, `glob`, `upload`, and `download`; and network/MCP terms such as `request`, `open_url`, `openUrl`, `urlopen`, and `httpClient`. This classifier is a guardrail and routing aid, not a substitute for Guardian or provider-side enforcement. If policy denies the tool exposure, the route is rejected and tools are not forwarded to the provider.

If `preferred_provider` is supplied, invalid references are hard errors. Unknown providers return `invalid_provider_reference`; unknown model aliases or direct model names return `invalid_model_reference`. A valid preferred provider remains a preference by default and may fall back under normal route behavior if it is ineligible, unhealthy, or returns an adapter error. Set `require_preferred_provider: true` or pass `--require-preferred-provider` to hard-lock that intent; if the preferred provider cannot be used, routing returns a structured error and does not fall back. Set `no_fallback: true` or pass `--no-fallback` to attempt only the first route candidate. `select()` and `route()` enforce the same hard-lock and no-fallback candidate semantics; `select()` is safe for callers that need pre-invocation selection.

## Audit Logging

Every route result includes an audit object. The CLI can persist sanitized JSONL audit records:

```bash
python scripts/hermes.py route --task general_reasoning --prompt "hello" --audit-log logs/hermes-audit.jsonl --json
```

Audit records include timestamp, selected provider and model, task type, requested capabilities, effective policy, Guardian decision fields, health-check status, dry-run status, fallback attempts, invocation status, and error category when present.

Audit sinks omit secret-like fields such as API keys, Authorization headers, tokens, credentials, and passwords. They also apply best-effort deterministic value redaction for bearer tokens, Basic auth, OpenAI-like `sk-...` keys, `x-api-key` headers, `client_secret`, `access_key`, lowercase `*_secret`, uppercase env assignments like `OPENAI_API_KEY=...`, `*_TOKEN=...`, `*_SECRET=...`, and `*_PASSWORD=...`, GitHub token prefixes such as `ghp_` and `github_pat_`, AWS-looking `AKIA...` access key IDs, credentials embedded in URLs, JWT-shaped three-segment tokens, authorization assignments with whitespace around separators, and quoted JSON fields for token/password/api_key/authorization. Known benign usage counters such as `prompt_tokens`, `completion_tokens`, and `total_tokens` are preserved. This redaction is not a license to log secrets: do not add prompt content, message bodies, full tool payloads, environment dumps, or raw credential-bearing request headers to audit events.

## Local Provider Trust Boundary

`allow_cloud: false` means the provider is local or private. Config validation fails fast if such a provider points outside the configured local trust boundary.

OpenAI-compatible provider `base_url` values must use `http` or `https`; schemes such as `file`, `ftp`, and `javascript` are rejected. `explicit_allowlist` host matching is exact after case-insensitive IDNA/lowercase normalization.

`local_trust_boundary` modes:

- `loopback_only`: accepts `localhost`, `127.0.0.1`, and `::1` only.
- `private_network`: backwards-compatible default; accepts loopback, RFC1918/private IPs, and `.local` hostnames.
- `explicit_allowlist`: requires `allowed_hosts` and accepts only listed hostnames.

Accepted `private_network` hosts:

- `localhost`
- `127.0.0.1`
- `::1`
- RFC1918 private ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- `.local` hostnames for explicitly local mDNS-style endpoints

Cloud providers such as OpenRouter must use `allow_cloud: true`.

The `private_network` check is syntactic and does not perform DNS resolution. Hostnames other than `localhost` and `.local` are not resolved to prove whether they are private.

Health URL construction preserves service-root `/health` for local bridges whose base URL ends in `/v1`, so `http://localhost:8781/v1` plus `/health` becomes `http://localhost:8781/health`. Other health/model endpoints remain under the configured base URL, so OpenRouter `https://openrouter.ai/api/v1` plus `/models` resolves to `https://openrouter.ai/api/v1/models`.

## Validation Modes

Routing dry-run:

- Default CLI behavior.
- Selects the planned provider without invoking `/v1/chat/completions`.
- Does not check bridge health unless `--check-health` is supplied.
- Dangerous routes are planning-only unless an injected Guardian returns `ALLOW`.

Dry-run with `--check-health`:

- Performs real `GET /health` checks.
- Still does not invoke `/v1/chat/completions`.
- Fails clearly when bridges are unavailable.

Config validation:

- `python scripts/hermes.py route --validate-config --json`
- Runs provider/routing consistency checks, including task-safety lint.
- Prints `{"issues": []}` for a clean config when `--json` is supplied.
- Exits nonzero if consistency or lint issues are found.
- Does not change normal routing behavior; advisory lint remains separate from route execution.

Mocked HTTP bridge integration:

- Test-local only.
- Uses an ephemeral in-process OpenAI-compatible HTTP server.
- Exercises `GET /health`, `GET /v1/models`, and `POST /v1/chat/completions` through adapter and route tests.
- Verifies adapter normalization and fallback behavior without requiring a real IDE bridge.
- Is not evidence that Cursor, VS Code, or any other real IDE worker bridge is running.

Real live worker bridge invocation:

- Requires `--invoke`.
- Performs real health checks and then posts to `/v1/chat/completions`.
- Dangerous invocations require Guardian `ALLOW`.
- `NOT_CHECKED` is planning-only and is never sufficient for dangerous live invocation.
- A successful mocked HTTP integration test is not evidence that a real IDE worker bridge is running.

**Do not claim cross-IDE live invocation is complete until at least one real worker bridge responds to `GET /health` and `POST /v1/chat/completions` under an explicit Guardian `ALLOW`.**
