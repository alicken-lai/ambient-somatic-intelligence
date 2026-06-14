# Git Hygiene Audit

## Current Observation

The worktree routinely contains live runtime files, generated reports, DMN memory, daemon state, and prompt scratch files. This is manageable only when commits are carefully scoped.

## Tracked

- Kernels and CLI code.
- Tests.
- Schemas and examples.
- Governance/rules docs.
- Selected release/audit reports.

## Should Usually Remain Uncommitted

- `logs/actions.jsonl`
- `logs/checksums.jsonl`
- `logs/dmn_reflection_cycle/`
- `state/`
- `memory/dmn.jsonl`
- `.codex_*_prompt.txt`
- `_run.txt`, `_v050_run.txt`

## Should Be Considered For Ignore Rules

- `.codex_*_prompt.txt`
- `_run.txt`
- `_v*_run.txt`
- `logs/dmn_reflection_cycle/`
- `state/daemon/*.lock`
- `*.out.log`, `*.err.log`

## Generated Reports

Generated reports are valuable but noisy. Recommendation: commit reports only when they represent named release/audit evidence, such as v0.9 integration audit.

## Risk

Without stricter ignore/snapshot policy, generated timestamp churn can hide meaningful code changes.

## Recommendation

Do not change `.gitignore` in this audit-only task. Open a follow-up hygiene PR with explicit operator approval.
