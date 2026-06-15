# Hermes-ASI v0.9.0-rc1 Governance Lock — Intentionally Immutable Constraints

> **Release**: Hermes-ASI v0.9.0-rc1
> **Document type**: Governance lock review
> **Scope**: All governance clauses intentionally kept unchanged for the rc1 release.
> **Companion docs**: `docs/release/KNOWN_LIMITATIONS.md`, `docs/release/V09_RELEASE_CHECKLIST.md`, `docs/release/TECH_DEBT_PRIORITY.md`

## 1. Purpose

This document enumerates every governance clause that is intentionally held
immutable at the v0.9.0-rc1 release point. It exists as an **anchor** so that
future phases can diff against a fixed baseline before introducing strategy
changes, Guardian policy edits, or memory doctrine shifts.

The lock is descriptive, not a runtime enforcement surface. Enforcement
continues to come from:

- `canonical_rules.md` (`canonical_version: 1.0.0`, `status: single_source_of_truth`)
- `guardian/policy.yaml` and related Guardian configuration files
- `hooks/guardian_gate.py` hard gateway over Shell / MCP / preToolUse
- Promotion gates, write gates, and verification independence requirements

Any change to items listed in Section 10 must go through the canonical_rules
promotion process, Guardian approval, and independent verification. rc1 does
not authorize any of these changes.

## 2. Guardian Authority

### 2.1 Risk classes

The Guardian risk classification surface is fixed to exactly three classes:

- `ALLOW`
- `REVIEW_REQUIRED`
- `BLOCK`

Classes cannot be added, removed, renamed, or reordered in rc1. Any new
intermediate state would require a canonical_rules revision and an explicit
governance review.

### 2.2 Policy contents (guardian/policy.yaml)

The Guardian policy defines three risk classes plus a blocked-keyword list
and a review-keyword list. The exact keyword tokens are intentionally **not**
reproduced in this document, because quoting them verbatim would re-trigger
the blocked-keyword classifier on this very file.

The canonical source of truth is `guardian/policy.yaml`. Read that file
directly for the exact keyword tokens. Both the blocked-keyword list and the
review-keyword list are frozen for rc1. Editing either list requires a
Guardian change policy review (see `docs/GUARDIAN_CHANGE_POLICY.md`) and an
rc-level sign-off.

### 2.3 Implementation surface

Guardian classification is implemented in `scripts/guardian_check.py`, which
reads:

- `guardian/policy.yaml` (primary policy)
- `guardian/decision_boundary.yaml` (decision boundary refinements)
- `guardian/allowed_paths.yaml` (allow-listed paths)
- `guardian/reflex_policy.yaml` (reflex engine policy)

Approval history is append-only at `guardian/approvals.jsonl`.

### 2.4 Hard gateway

`hooks/guardian_gate.py` is the **hard** Guardian gateway in rc1. It covers:

- Shell commands
- MCP tool invocations
- Subset of preToolUse events

The hard gateway cannot be bypassed by provider, kernel, or operator intent
within rc1. If the gateway is unreachable, the agent must report the failure
and request remediation rather than take an alternate path.

## 3. Approval Boundaries

### 3.1 Operations that require approval

Per `canonical_rules.md` Section 2.2, the following operations require Guardian
classification before execution:

- File write / modify / removal
- Outbound send (messages, network calls with side effects)
- Package install (pip, brew, etc.)
- Git commit / push / merge

### 3.2 Read-only operations (no approval required)

Per Section 2.3, these are exempt from approval:

- File read
- Search (Grep / Glob)
- Memory recall (`memory_recall`, `dmn_search`)
- Non-mutating state reads
- Browser snapshot

### 3.3 Outbound messaging double confirmation

Per Section 2.4, outbound messaging requires **double confirmation**:

1. Guardian classifies the action.
2. The full message body is shown to the operator.
3. The operator gives explicit consent.
4. Only then may `messages_send` proceed.

### 3.4 BLOCK is not bypassable

Per Section 2.5, any `BLOCK` classification is terminal within rc1. There is
no override path. Reclassification requires a governed policy edit, not a
runtime workaround.

## 4. Provider Restrictions

### 4.1 CLI adapter only

Providers communicate exclusively through CLI adapters:

- `hermes/providers/cli_adapter.py`
- `hermes/providers/cli_discovery.py`
- `hermes/providers/base.py`

Orchestration flows through `RoutingEngine`, `RoutePolicy`, and
`ProviderRequest`. There is no in-process LLM provider bundled with the
kernel.

### 4.2 route --invoke is the single trigger

`route --invoke` is the only command that triggers an actual provider call.
It must pass Guardian classification. No other entry point may invoke a
provider directly within rc1.

### 4.3 No production credentials in providers

Providers do not hold production credentials. All credentials come from the
environment. `Hermes-ASI` itself does not carry production credentials; the
`user-hermes-asi` MCP server uses environment authentication.

### 4.4 Route policy flags

Provider capability is constrained by route policy flags:

- `--max-cost-tier`
- `--disallow-cloud`
- `--allow-*` capability flags

These flags are part of the locked routing contract for rc1.

## 5. Credential Restrictions

- `.env`, `credentials.json`, and any secret-bearing files are forbidden from
  being committed (Git Safety, Section 8 of canonical_rules.md).
- `Hermes-ASI` does not hold production credentials itself.
- The `user-hermes-asi` MCP server authenticates via environment variables.
- Credential rotation and injection is an operator responsibility, not a
  kernel runtime action.

## 6. Memory Write Policies

### 6.1 Append-only DMN

`memory/dmn.jsonl` is append-only within rc1. Edits or removals require a
governed repair flow; silent erasure is forbidden.

### 6.2 English-only DMN content

DMN memory content must be written in English to avoid encoding corruption
and mixed-script recall noise. User-facing conversation may remain in
Traditional Chinese, but the persisted DMN record is English.

### 6.3 Operator-mediated append path

Kernels do not autonomously write DMN. Only the operator or Hermes-mediated
append path may append records.

### 6.4 Schema validation before write

Writes pass schema validation through:

- `schemas/dmn_event.schema.json`
- `tools/validate_dmn_events.py`

Invalid records are rejected at the validator boundary.

### 6.5 No silent erasure

Per canonical_rules Sections 3 and 6.3, no agent may erase memory silently.
Any memory correction must go through governed repair.

### 6.6 Strategic memory gates

Strategic memory writes must pass:

- `strategic_write_gate`
- Promotion guards in `memory/ontology/promotion_*.py`
- `governance/doctrine/promotion_verification_gate.py`

## 7. Verification Independence

Per canonical_rules Section 5: the implementer is an LLM and must not
self-verify.

- The implementer of a change cannot also be its verifier.
- Independent verifiers use a **separate context**, objective criteria, and a
  distinct `verifier_id`.
- Confidence is tracked per verification.
- Low confidence blocks promotion.

There is no "self-verify then promote" path in rc1.

## 8. Reality Replay Freeze

### 8.1 P1 freeze axioms

Per canonical_rules Section 6.1, the P1 freeze holds the following axioms:

1. Memory and audit trails are append-only.
2. No autonomous corrective action.
3. Guardian approval required for any external action.
4. The implementer must not verify itself.
5. Strategy is earned, not injected.
6. Reality replay gates cannot be bypassed.
7. Historical failures are not hidden.
8. `BOOTSTRAP_GAP` is a recognized gap state, not a silent fill.

### 8.2 BOOTSTRAP_GAP vs DAEMON_FAILURE

Per Section 6.2:

- `BOOTSTRAP_GAP` indicates the system lacks sufficient bootstrap evidence to
  assert a state; it must be reported, not filled by interpolation.
- `DAEMON_FAILURE` indicates a daemon-side runtime failure.
- The two must not be conflated in operational scoring.

### 8.3 Forbidden in replay

Per Section 6.3, during replay the following are forbidden:

- Interpolation of missing events
- Hiding historical failures
- Reclassification without governance review

## 9. Cross-Cutting Source References

| Item | Primary source file |
|------|---------------------|
| Canonical rules | `hermes/rules/canonical_rules.md` |
| Guardian policy | `guardian/policy.yaml` |
| Decision boundary | `guardian/decision_boundary.yaml` |
| Allowed paths | `guardian/allowed_paths.yaml` |
| Reflex policy | `guardian/reflex_policy.yaml` |
| Guardian implementation | `scripts/guardian_check.py` |
| Hard gateway | `hooks/guardian_gate.py` |
| Permission enforcer | `kernel/isolation/permission_enforcer.py` |
| Root policy | `kernel/isolation/root_policy.py` |
| State guard | `kernel/isolation/state_guard.py` |
| Write guard | `kernel/isolation/write_guard.py` |
| Approval log | `guardian/approvals.jsonl` |
| DMN schema | `schemas/dmn_event.schema.json` |
| DMN validator | `tools/validate_dmn_events.py` |
| Promotion guards | `memory/ontology/promotion_*.py` |
| Promotion verification | `governance/doctrine/promotion_verification_gate.py` |

## 10. What Is Intentionally Immutable in v0.9.0-rc1

| Item | Source | Mutability |
|------|--------|------------|
| `canonical_rules.md` v1.0.0 | `hermes/rules/` | Frozen for rc1 |
| Guardian risk classes | `guardian/policy.yaml` | Frozen |
| Blocked keyword list | `guardian/policy.yaml` | Frozen |
| Review keyword list | `guardian/policy.yaml` | Frozen |
| Memory append-only doctrine | `canonical_rules` Section 3, Section 6.1 | Frozen |
| `BOOTSTRAP_GAP` doctrine | `canonical_rules` Section 6.2 | Frozen |
| Verification independence | `canonical_rules` Section 5 | Frozen |
| Promotion chain L1 -> L2 -> L3 -> L4 | `canonical_rules` Section 4 | Frozen |
| Outbound messaging double confirmation | `canonical_rules` Section 2.4 | Frozen |
| DMN English-only | `canonical_rules` Section 3 | Frozen |
| Schema set (9 schemas) | `schemas/` | Frozen for rc1 |

### 10.1 Changing any locked item

To change a locked item in a future phase:

1. File a governed change proposal.
2. Pass Guardian classification on the proposal itself.
3. Obtain independent verification with a separate verifier.
4. Update `canonical_rules.md` version and `canonical_version` field.
5. Re-baseline this lock document with the new release tag.

rc1 does not perform any of these steps.
