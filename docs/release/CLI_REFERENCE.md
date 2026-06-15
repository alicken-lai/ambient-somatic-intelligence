# Hermes-ASI v0.9.0-rc1 CLI Reference

> Scope: this document is the authoritative reference for the command-line interface shipped with Hermes-ASI v0.9.0-rc1.
> SSOT for command surface: `scripts/hermes.py` (argparse-based, flat-layout project).
> Release documentation only. This file does not modify kernel code, governance rules, Guardian settings, or permissions.

## 1. Overview

The Hermes-ASI CLI entry point is a single script:

```
python scripts/hermes.py <command> [options]
```

Characteristics:

- Flat-layout project. There is no `pip` console-script entry point and no installed `hermes` executable.
- All commands must be executed from the project root (`C:\Users\User\ambient-somatic-intelligence`), or with `PYTHONPATH` set to the project root so that `hermes.*` kernel packages resolve.
- The CLI is `argparse`-based with subcommands. As of v0.9.0-rc1 there are **29 subcommands** in total: 1 provider orchestration command (`route`), 1 deliberation execution command (`deliberate`), and 27 advisory report commands (`*-report`).
- Every subcommand accepts a shared `--json` flag to switch between human-readable Markdown and machine-readable JSON output.

## 2. Global Conventions

| Convention | Detail |
|---|---|
| Invocation | `python scripts/hermes.py <command> [flags]` from project root |
| Working directory | Project root, or set `PYTHONPATH=<project root>` |
| Output switch | `--json` toggles JSON (default: Markdown) for any command that emits a report |
| Default output root | `reports/` under the project root |
| Side effects | All `*-report` commands are advisory-only (read + write to `reports/`). Only `route --invoke` triggers external provider calls. |
| Guardian interaction | `route --invoke` requires a Guardian `ALLOW`. Report commands do not require Guardian pre-checks for external side effects because they have none. |
| Exit codes | `0` on success, non-zero on argparse error, missing input, or kernel exception. |

## 3. Command Groups

Commands are organized by functional layer. Group membership is used by this document only for navigation; the CLI itself is flat.

| Group | Commands |
|---|---|
| Provider Orchestration | `route` |
| Deliberation Execution | `deliberate` |
| Deliberation Reports | `deliberate-report`, `routing-report`, `roi-report`, `strategy-report`, `playbook-report`, `skill-report`, `failure-report` |
| Verification Reports | `evidence-report`, `claim-report`, `verification-report`, `contradiction-report` |
| Acquisition Reports | `acquisition-report`, `evidence-quality-report`, `knowledge-index-report` |
| Calibration Reports | `knowledge-health-report`, `trust-report`, `drift-report` |
| Reality Alignment Reports | `fitness-report`, `reality-report`, `diversity-report` |
| Identity Reports | `identity-report`, `continuity-report`, `life-history-report` |
| Institutional Reports | `audit-report`, `graph-health-report`, `release-report` |

## 4. Provider Orchestration

### 4.1 `route`

**Description.** Select and optionally invoke a provider for a task against the configured provider registry and routing rules.

**Inputs.**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--task` | string | required | Task description used for routing |
| `--prompt` | string | optional | Full prompt to send if invoking |
| `--registry` | path | `config/provider_registry.yaml` | Provider registry YAML |
| `--rules` | path | `config/routing_rules.yaml` | Routing rules YAML |
| `--capability` | multi-string | optional | Required capabilities (repeatable) |
| `--preferred-provider` | string | optional | Preferred provider id |
| `--require-preferred-provider` | flag | off | Fail if preferred provider unavailable |
| `--no-fallback` | flag | off | Disable fallback to secondary providers |
| `--max-cost-tier` | enum | unset | `low` / `medium` / `high` |
| `--disallow-cloud` | flag | off | Exclude cloud providers |
| `--allow-local-file-access` | flag | off | Permit local file access capability |
| `--allow-code-modification` | flag | off | Permit code modification capability |
| `--allow-terminal-execution` | flag | off | Permit terminal execution capability |
| `--allow-mcp-tools` | flag | off | Permit MCP tool capability |
| `--validate-config` | flag | off | Validate registry and rules then exit |
| `--invoke` | flag | off | **Execute** the selected provider (Guardian-gated) |
| `--check-health` | flag | off | Probe provider health before routing |
| `--audit-log` | path | optional | Append routing decision to audit log |
| `--json` | flag | off | Emit JSON instead of human-readable text |

**Outputs.** Routing decision (and, if `--invoke`, provider response) to stdout. Optional audit log line at `--audit-log`.

**Report Generation.** No report file. Uses `hermes/orchestration` routing kernel and `hermes/providers` adapters.

**Safety Considerations.** Without `--invoke`, this command is advisory-only (planning + validation). With `--invoke`, it performs an external provider call and **must** pass Guardian with `risk == ALLOW` before execution. Capability-expanding flags (`--allow-local-file-access`, `--allow-code-modification`, `--allow-terminal-execution`, `--allow-mcp-tools`) widen the capability envelope and are themselves subject to Guardian review.

## 5. Deliberation Execution

### 5.1 `deliberate`

**Description.** Run the ASI Deliberation Layer for a task.

**Inputs.**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | positional string | required | Task to deliberate on |
| `--mode` | enum | `light` | `single` / `light` / `full` / `guardian_required` |
| `--dry-run` | flag | off | Do not persist artifacts |
| `--show-trace` | flag | off | Print the deliberation trace |
| `--providers` | string | optional | Comma-separated provider list override |
| `--no-save-trace` | flag | off | Do not persist the trace |
| `--registry` | path | optional | Override provider registry |
| `--config` | path | `config/deliberation.yaml` | Deliberation config |
| `--json` | flag | off | Emit JSON |

**Outputs.** Deliberation trace (persisted unless `--no-save-trace` / `--dry-run`); printed to stdout if `--show-trace`.

**Report Generation.** Uses `hermes/deliberation` kernel. Trace artifacts feed downstream `*-report` commands.

**Safety Considerations.** No external side effects. Purely advisory unless a selected provider is invoked by the deliberation kernel (separate from this CLI command).

## 6. Deliberation Reports

### 6.1 `deliberate-report`

**Description.** Evaluate golden traces and write a deliberation quality report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--benchmarks` | path | `tests/golden_traces/benchmarks.json` | Golden trace benchmarks |
| `--output` | path | `reports/deliberation_quality_report.md` | Output report path |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/deliberation_quality_report.md` (or `.json` with `--json`).

**Report Generation.** `hermes/deliberation` quality generators over `tests/golden_traces/`.

**Safety Considerations.** Advisory-only. Reads benchmark fixtures, writes report.

### 6.2 `routing-report`

**Description.** Generate the adaptive routing learning report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--benchmarks` | path | optional | Override benchmarks |
| `--output` | path | `reports/deliberation_learning_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/deliberation_learning_report.md`.

**Report Generation.** `hermes/deliberation` learning generators.

**Safety Considerations.** Advisory-only.

### 6.3 `roi-report`

**Description.** Generate ROI and effectiveness summary.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--benchmarks` | path | optional | Override benchmarks |
| `--output` | path | `reports/deliberation_roi_report.md` | Markdown output |
| `--json-output` | path | `reports/deliberation_roi_report.json` | JSON output |
| `--json` | flag | off | Switch primary output to JSON |

**Outputs.** `reports/deliberation_roi_report.md` and `reports/deliberation_roi_report.json`.

**Report Generation.** `hermes/deliberation` ROI generators.

**Safety Considerations.** Advisory-only.

### 6.4 `strategy-report`

**Description.** Explain the adaptive strategy for a specific task.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | positional string | required | Task text |
| `--task-class` | string | `architecture` | Task class hint |
| `--risk-level` | enum | `normal` | `normal` / `high` |
| `--output` | path | `reports/deliberation_strategy_report.md` | Markdown output |
| `--json-output` | path | `reports/deliberation_strategy_report.json` | JSON output |
| `--json` | flag | off | Switch primary output to JSON |

**Outputs.** `reports/deliberation_strategy_report.md` and `reports/deliberation_strategy_report.json`.

**Report Generation.** `hermes/deliberation` strategy generators.

**Safety Considerations.** Advisory-only.

### 6.5 `playbook-report`

**Description.** Generate the deliberation playbook report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/playbook_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/playbook_report.md` (and `.json` when requested).

**Report Generation.** `hermes/deliberation` playbook generators.

**Safety Considerations.** Advisory-only.

### 6.6 `skill-report`

**Description.** Generate the deliberation skill report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/skill_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/skill_report.md` (and `.json`).

**Report Generation.** `hermes/deliberation` skill generators.

**Safety Considerations.** Advisory-only.

### 6.7 `failure-report`

**Description.** Generate the deliberation failure learning report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/failure_learning_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/failure_learning_report.md` (and `.json`).

**Report Generation.** `hermes/deliberation` failure-learning generators.

**Safety Considerations.** Advisory-only.

## 7. Verification Reports

### 7.1 `evidence-report`

**Description.** Generate the evidence quality report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/evidence_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/evidence_report.md` and `reports/evidence_report.json`.

**Report Generation.** `hermes/verification/reports.py` evidence generators.

**Safety Considerations.** Advisory-only.

### 7.2 `claim-report`

**Description.** Generate the claim registry report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/claim_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/claim_report.md` and `reports/claim_report.json`.

**Report Generation.** `hermes/verification/reports.py` claim generators.

**Safety Considerations.** Advisory-only.

### 7.3 `verification-report`

**Description.** Generate the verification coverage report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/verification_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/verification_report.md` and `reports/verification_report.json`.

**Report Generation.** `hermes/verification/reports.py` coverage generators.

**Safety Considerations.** Advisory-only.

### 7.4 `contradiction-report`

**Description.** Generate the contradiction report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/contradiction_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/contradiction_report.md` and `reports/contradiction_report.json`.

**Report Generation.** `hermes/verification/reports.py` contradiction generators.

**Safety Considerations.** Advisory-only.

## 8. Acquisition Reports

### 8.1 `acquisition-report`

**Description.** Generate the evidence acquisition report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/acquisition_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/acquisition_report.md` and `reports/acquisition_report.json`.

**Report Generation.** `hermes/acquisition/reports.py` acquisition generators.

**Safety Considerations.** Advisory-only.

### 8.2 `evidence-quality-report`

**Description.** Generate the evidence quality acquisition report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/evidence_quality_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/evidence_quality_report.md` and `reports/evidence_quality_report.json`.

**Report Generation.** `hermes/acquisition/reports.py` evidence-quality generators.

**Safety Considerations.** Advisory-only.

### 8.3 `knowledge-index-report`

**Description.** Generate the internal knowledge index report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/knowledge_index_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/knowledge_index_report.md` (and `.json`).

**Report Generation.** `hermes/acquisition/reports.py` knowledge-index generators.

**Safety Considerations.** Advisory-only.

## 9. Calibration Reports

### 9.1 `knowledge-health-report`

**Description.** Generate the calibrated knowledge health report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/knowledge_health_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/knowledge_health_report.md` and `reports/knowledge_health_report.json`.

**Report Generation.** `hermes/calibration` health generators.

**Safety Considerations.** Advisory-only.

### 9.2 `trust-report`

**Description.** Generate the trust calibration report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/trust_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/trust_report.md` and `reports/trust_report.json`.

**Report Generation.** `hermes/calibration` trust generators.

**Safety Considerations.** Advisory-only.

### 9.3 `drift-report`

**Description.** Generate the knowledge drift report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/drift_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/drift_report.md` and `reports/drift_report.json`.

**Report Generation.** `hermes/calibration` drift generators.

**Safety Considerations.** Advisory-only.

## 10. Reality Alignment Reports

### 10.1 `fitness-report`

**Description.** Generate the institutional fitness report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/institutional_fitness_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/institutional_fitness_report.md` and `reports/institutional_fitness_report.json`.

**Report Generation.** `hermes/reality_alignment` fitness generators.

**Safety Considerations.** Advisory-only.

### 10.2 `reality-report`

**Description.** Generate the reality alignment report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/reality_alignment_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/reality_alignment_report.md` and `reports/reality_alignment_report.json`.

**Report Generation.** `hermes/reality_alignment` alignment generators.

**Safety Considerations.** Advisory-only.

### 10.3 `diversity-report`

**Description.** Generate the knowledge diversity report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/diversity_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/diversity_report.md` and `reports/diversity_report.json`.

**Report Generation.** `hermes/reality_alignment` diversity generators.

**Safety Considerations.** Advisory-only.

## 11. Identity Reports

### 11.1 `identity-report`

**Description.** Generate the narrative identity report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/identity_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/identity_report.md` (and `.json`).

**Report Generation.** `hermes/identity` identity generators.

**Safety Considerations.** Advisory-only.

### 11.2 `continuity-report`

**Description.** Generate the identity continuity report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/continuity_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/continuity_report.md` and `reports/continuity_report.json`.

**Report Generation.** `hermes/identity` continuity generators.

**Safety Considerations.** Advisory-only.

### 11.3 `life-history-report`

**Description.** Generate the institutional life-history report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/life_history_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/life_history_report.md` and `reports/life_history_report.json`.

**Report Generation.** `hermes/identity` life-history generators.

**Safety Considerations.** Advisory-only.

## 12. Institutional Reports

### 12.1 `audit-report`

**Description.** Generate the Hermes-ASI v0.9 integration audit report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/institutional_audit_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/institutional_audit_report.md` and `reports/institutional_audit_report.json`.

**Report Generation.** `hermes/audit` integration audit generators.

**Safety Considerations.** Advisory-only.

### 12.2 `graph-health-report`

**Description.** Generate the knowledge graph health report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/graph_health_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/graph_health_report.md` and `reports/graph_health_report.json`.

**Report Generation.** `hermes/graph` health generators.

**Safety Considerations.** Advisory-only.

### 12.3 `release-report`

**Description.** Generate the Hermes-ASI v0.9 RC release report.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--output` | path | `reports/v09_release_report.md` | Output |
| `--json` | flag | off | Emit JSON |

**Outputs.** `reports/v09_release_report.md` and `reports/v09_release_report.json`.

**Report Generation.** `hermes/release` generators.

**Safety Considerations.** Advisory-only.

## 13. Safety Summary

The CLI surface partitions cleanly into two safety tiers:

| Tier | Commands | Behavior |
|---|---|---|
| Advisory (read + write report) | `route` (without `--invoke`), `deliberate`, and all 27 `*-report` commands | Read inputs, generate report artifacts under `reports/`, no external side effects, no Guardian `ALLOW` required for external action |
| External action (provider call) | `route --invoke` | Performs a real provider invocation. **Requires Guardian `risk == ALLOW` before execution.** Capability-expanding flags are reviewed alongside the invocation. |

Operational guidance:

- Treat all `*-report` commands as safe to run for inspection and audit. They never call external providers, never mutate kernel state, and never modify governance files.
- The only externally observable action initiated by the CLI is `route --invoke`. All capability-granting flags (`--allow-local-file-access`, `--allow-code-modification`, `--allow-terminal-execution`, `--allow-mcp-tools`) must be reviewed explicitly when used with `--invoke`.
- `deliberate` itself does not perform external calls via this CLI surface; if the deliberation kernel ever delegates to a provider, that path is governed by the kernel and the Guardian hook layer, not by this CLI command.
