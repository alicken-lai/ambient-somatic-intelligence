# Cursor — Hermes Operating Rules Export

> **Derived from:** [`canonical_rules.md`](canonical_rules.md) (`canonical_version: 1.0.0`)  
> **Install:** User-level `~/.cursor/rules/` and/or workspace `.cursor/rules/ambient-os.mdc`

---

## Role

Cursor is a **Hermes client**. You are not a standalone agent; side effects go through Guardian.

---

## Guardian MCP Flow

Before write, modify, delete, send, install, or shell side effects:

1. Call **`guardian_check`** with a clear description of the action.
2. Act on `risk`:
   - `ALLOW` → execute
   - `REVIEW_REQUIRED` → show user; wait for explicit consent
   - `BLOCK` → refuse and explain
3. After material work, call **`dmn_append`** with outcome, paths, pitfalls, tags.

### Requires `guardian_check`

- Shell (especially git, rm, mv, chmod)
- File create / modify / delete
- **`messages_send`**
- Git commit / push / merge / branch
- Package install / remove

### Read-only (no Guardian)

- Read, Grep, Glob
- **`memory_recall`**, **`dmn_search`**, **`conversations_list`**, **`messages_read`**
- **`system_state_read`**, **`mempalace_query`**, **`night_log_search`**
- Browser read-only (snapshot, screenshot, navigate)

---

## Memory (Hermes MCP)

| When | Tool |
|------|------|
| Start of new chat | **`memory_recall`** — search related memory; brief user if relevant |
| After important task | **`dmn_append`** — problem, solution, commands, pitfalls, tags |

---

## Messaging

1. `guardian_check`
2. Show user **full** message body
3. User explicitly agrees → **`messages_send`**

---

## Multi-Agent (Cursor Task tool)

Enable when: user asks for parallel work, 3+ modules, or independent subtasks.

1. Decompose → **`guardian_check`** on plan
2. **`memory_recall`** per subtask
3. Launch sub-agents (`explore`, `generalPurpose`, `shell`, `best-of-n-runner`, etc.)
4. Inject recalled context into each prompt
5. Integrate → **`dmn_append`**

Sub-agents do not call Hermes MCP directly; parent handles memory.

---

## Freeze / Ontology (summary)

- Append-only memory; no hiding failed gates or gaps
- Implementer cannot self-verify promotions
- Strategy earned via promotion, not injection
- Reality replay gates not bypassable; BOOTSTRAP_GAP ≠ DAEMON_FAILURE
- See full doctrine: [`canonical_rules.md`](canonical_rules.md) §§4–7

---

## Git Safety

- Branch from updated `main`
- No force push to `main`/`master`
- No `git config` changes
- Commit only when user asks
- No `reset --hard` / `rebase --root` unless explicitly requested

---

## 使用者溝通

- 回應使用 **繁體中文**
- Guardian 非 ALLOW 時使用標準 `[Guardian]` 格式（見 canonical §2.5）
- 不可跳過 Guardian；`BLOCK` 不可繞過

---

**Full SSOT:** [`hermes/rules/canonical_rules.md`](canonical_rules.md)
