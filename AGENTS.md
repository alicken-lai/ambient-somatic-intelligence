# AMBIENT SOMATIC INTELLIGENCE

## Project Constitution

1. Safety First.
2. Never execute destructive commands.
3. Ask Guardian before external action.
4. All actions logged.
5. Memory append-only.
6. CLI preferred over GUI.
7. GUI actions require CUA sandbox.

## Canonical Operating Rules (SSOT)

Full portable agent doctrine lives at **[`hermes/rules/canonical_rules.md`](hermes/rules/canonical_rules.md)** (`canonical_version: 1.0.0`).

That document covers: Hermes/Guardian flow, memory doctrine, ontology promotion, independent verification, P1 reality-replay freeze (including BOOTSTRAP_GAP), telemetry discipline, git safety, multi-agent orchestration, and 繁體中文 user communication.

## IDE-specific views

| IDE / tool | File |
|------------|------|
| Cursor | [`hermes/rules/cursor_rules_export.md`](hermes/rules/cursor_rules_export.md), [`.cursor/rules/ambient-os.mdc`](.cursor/rules/ambient-os.mdc) |
| VS Code / Copilot | [`.github/copilot-instructions.md`](.github/copilot-instructions.md) |
| Codex | [`hermes/rules/codex_agents.md`](hermes/rules/codex_agents.md) |
| Antigravity | [`hermes/rules/antigravity_rules.md`](hermes/rules/antigravity_rules.md) |

Sync policy and port checklist: [`hermes/rules/rule_sync_map.md`](hermes/rules/rule_sync_map.md).

## Agent quick constraints

- For substantive questions, inspect current context first; if insufficient, query Hermes/DMN memory before external web resources.
- Keep DMN memory active for repeated topics, operator preferences, project history, unresolved ambiguity, and prior incidents.
- Write all DMN memory records in English, even when user-facing conversation is Chinese, to avoid encoding corruption and mixed-script recall noise.
- Implementer must not self-verify promotions or gate PASS claims.
- Strategy is earned through promotion, not injected.
- Reality replay gates are not bypassable; historical failures are not hidden.
- Commit only when the user asks; no force-push to `main`; no `git config` changes.
