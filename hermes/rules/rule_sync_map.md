# Rule Sync Map — Manual Port Guide

> **Policy:** `canonical_first_manual_port` — edit [`canonical_rules.md`](canonical_rules.md) first, then port to IDE targets. Do not edit derived files in isolation without updating canonical.

---

## Hierarchy

```
hermes/rules/canonical_rules.md          ← SSOT (edit here)
├── cursor_rules_export.md               ← Cursor user rules reference
├── .cursor/rules/ambient-os.mdc         ← Cursor workspace (alwaysApply)
├── vscode_copilot_instructions.md       ← source for Copilot
├── .github/copilot-instructions.md      ← GitHub Copilot install path
├── codex_agents.md                      ← Codex long-form
├── antigravity_rules.md                 ← Antigravity agent-first
└── AGENTS.md                            ← short Codex/project summary + pointer
```

---

## File → IDE setting

| Canonical section | Cursor | VS Code / Copilot | Codex | Antigravity |
|-------------------|--------|-------------------|-------|-------------|
| Constitution | `ambient-os.mdc` + optional `~/.cursor/rules/hermes-integration.mdc` | `.github/copilot-instructions.md` | `AGENTS.md` + `codex_agents.md` | `antigravity_rules.md` |
| Guardian flow | `cursor_rules_export.md` (MCP names) | Generic "request approval" in copilot-instructions | `codex_agents.md` workflow table | Escalation table in antigravity |
| Memory | MCP: `memory_recall`, `dmn_append` | "Suggest log append" | Recall + log in workflow | Parent records for sub-agents |
| Freeze / replay | §6 in canonical | § in copilot-instructions | Hard prohibitions in codex | No self-verify + replay respect |
| Git safety | All Cursor files | copilot-instructions | AGENTS + codex | Escalation triggers |
| 繁體中文 | cursor export + ambient-os.mdc | copilot Communication section | codex workflow | antigravity Communication |

---

## Port checklist (per change)

1. [ ] Update `canonical_rules.md` and bump `canonical_version` if breaking
2. [ ] Port to `cursor_rules_export.md` and `.cursor/rules/ambient-os.mdc`
3. [ ] Port to `vscode_copilot_instructions.md` and `.github/copilot-instructions.md` (keep in sync)
4. [ ] Port to `codex_agents.md` and skim `AGENTS.md` summary
5. [ ] Port to `antigravity_rules.md` if autonomy boundaries changed
6. [ ] Update `rule_manifest.json` `last_updated` (ISO8601)
7. [ ] Run `python hermes/rules/validate_rules.py` or `pytest tests/test_hermes_rules.py`

---

## User-level Cursor rules (outside repo)

The file `~/.cursor/rules/hermes-integration.mdc` is **not** in this repository. After canonical updates:

1. Diff against [`cursor_rules_export.md`](cursor_rules_export.md)
2. Manually merge MCP-specific sections into user-level rule
3. Keep workspace [`ambient-os.mdc`](../../.cursor/rules/ambient-os.mdc) for project-specific freeze pointers

---

## Validation

```bash
python hermes/rules/validate_rules.py
# or
pytest tests/test_hermes_rules.py -q
```

---

## Manifest

See [`rule_manifest.json`](rule_manifest.json) for machine-readable file list.
