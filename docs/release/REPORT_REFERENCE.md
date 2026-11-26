# Hermes-ASI v0.9.0-rc1 Report Reference

> Scope: authoritative inventory of all report artifacts produced by Hermes-ASI v0.9.0-rc1.
> Source of truth for the report surface: `scripts/hermes.py` (`*-report` subcommands) plus kernel-level generators under `hermes/`.
> Release documentation only. This file does not modify kernel code, governance rules, Guardian settings, or permissions.

## 1. Overview

This document inventories every report artifact that the v0.9.0-rc1 release can produce. Reports are grouped by the kernel layer that owns them. For each report the table records:

- **Report** — file name (both `.md` and `.json` are listed where both formats exist).
- **Source Kernel** — the kernel module whose generator function produces the artifact (e.g., `hermes/verification/reports.py`).
- **Format** — `Markdown`, `JSON`, or `Both`.
- **Purpose** — one-sentence description.
- **Retention Value** — `High` (audit / legal / governance interest), `Medium` (operational / release-tracking interest), `Low` (ad-hoc or debug).

Retention values are advisory metadata for operators curating long-term storage. They are not enforced by the CLI.

## 2. Deliberation Layer

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `deliberation_quality_report.md` / `.json` | `hermes/deliberation` | Both | Evaluate golden traces and report deliberation quality | High |
| `deliberation_strategy_report.md` / `.json` | `hermes/deliberation` | Both | Explain the adaptive strategy selected for a task | Medium |
| `deliberation_roi_report.md` / `.json` | `hermes/deliberation` | Both | Summarize ROI and effectiveness of the deliberation layer | Medium |
| `deliberation_learning_report.md` | `hermes/deliberation` | Markdown | Adaptive routing learning summary | Medium |
| `playbook_report.md` / `.json` | `hermes/deliberation` | Both | Deliberation playbook reference | Medium |
| `skill_report.md` / `.json` | `hermes/deliberation` | Both | Deliberation skill registry summary | Medium |
| `failure_learning_report.md` | `hermes/deliberation` | Markdown | Failure-mode learning summary | High |
| `deliberation_ab_results.json` | `hermes/deliberation` | JSON | A/B comparison results between deliberation modes | Medium |
| `deliberation_skill_registry.json` | `hermes/deliberation` | JSON | Canonical skill registry snapshot | Medium |

## 3. Verification Layer

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `evidence_report.md` / `.json` | `hermes/verification/reports.py` | Both | Evidence quality summary | High |
| `claim_report.md` / `.json` | `hermes/verification/reports.py` | Both | Claim registry summary | High |
| `verification_report.md` / `.json` | `hermes/verification/reports.py` | Both | Verification coverage summary | High |
| `contradiction_report.md` / `.json` | `hermes/verification/reports.py` | Both | Detected contradictions across claims | High |
| `evidence_quality_report.md` / `.json` | `hermes/acquisition/reports.py` | Both | Evidence quality from the acquisition pipeline | High |

## 4. Acquisition Layer

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `acquisition_report.md` / `.json` | `hermes/acquisition/reports.py` | Both | Evidence acquisition pipeline summary | Medium |
| `knowledge_index_report.md` | `hermes/acquisition/reports.py` | Markdown | Internal knowledge index summary | Medium |
| `knowledge_health_report.md` / `.json` | `hermes/calibration` | Both | Calibrated knowledge health summary | Medium |

## 5. Calibration Layer

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `trust_report.md` / `.json` | `hermes/calibration` | Both | Trust calibration summary | High |
| `drift_report.md` / `.json` | `hermes/calibration` | Both | Knowledge drift detection summary | Medium |

## 6. Reality Alignment Layer

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `reality_alignment_report.json` | `hermes/reality_alignment` | JSON | Reality alignment scoring snapshot | High |
| `diversity_report.md` / `.json` | `hermes/reality_alignment` | Both | Knowledge diversity summary | Medium |
| `institutional_fitness_report.md` / `.json` | `hermes/reality_alignment` | Both | Institutional fitness scoring summary | High |

## 7. Identity Layer

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `identity_report.md` | `hermes/identity` | Markdown | Narrative identity summary | Medium |
| `identity_registry.json` | `hermes/identity` | JSON | Canonical identity registry snapshot | High |
| `continuity_report.md` / `.json` | `hermes/identity` | Both | Identity continuity summary | High |
| `life_history_report.md` / `.json` | `hermes/identity` | Both | Institutional life-history narrative | High |

## 8. Registries (cross-kernel)

Cross-kernel registries are append-only SSOT artifacts. They are read by multiple report generators and updated by their owning kernels.

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `belief_registry.json` | `hermes/verification` (primary) | JSON | Canonical belief registry | High |
| `trust_registry.json` | `hermes/calibration` (primary) | JSON | Canonical trust registry | High |
| `evidence_registry.json` | `hermes/verification` (primary) | JSON | Canonical evidence registry | High |

## 9. Institutional Audit

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `institutional_audit_report.md` / `.json` | `hermes/audit` | Both | v0.9 integration audit summary | High |
| `institutional_fitness_report.md` / `.json` | `hermes/reality_alignment` | Both | Institutional fitness scoring (also listed under Reality Alignment) | High |

## 10. Graph Health

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `graph_health_report.md` / `.json` | `hermes/graph` | Both | Knowledge graph health summary | High |

## 11. Release Health

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `v09_release_report.md` / `.json` | `hermes/release` | Both | Hermes-ASI v0.9 RC release report | High |

## 12. DMN Governance

| Report | Source Kernel | Format | Purpose | Retention Value |
|---|---|---|---|---|
| `dmn_event_validation_report.json` | `hermes/dmn` governance | JSON | DMN event schema validation results | High |

## 13. Cross-References

The following is the complete alphabetical list of report filenames producible by v0.9.0-rc1. Files marked with `*` are produced directly by `scripts/hermes.py` `*-report` subcommands; others are generated by kernel pipelines or are persistent registry snapshots consumed by report generators.

```
acquisition_report.json
acquisition_report.md
belief_registry.json
claim_report.json
claim_report.md
continuity_report.json
continuity_report.md
contradiction_report.json
contradiction_report.md
deliberation_ab_results.json
deliberation_learning_report.md
deliberation_quality_report.json
deliberation_quality_report.md
deliberation_roi_report.json
deliberation_roi_report.md
deliberation_skill_registry.json
deliberation_strategy_report.json
deliberation_strategy_report.md
diversity_report.json
diversity_report.md
dmn_event_validation_report.json
drift_report.json
drift_report.md
evidence_quality_report.json
evidence_quality_report.md
evidence_registry.json
evidence_report.json
evidence_report.md
failure_learning_report.md
graph_health_report.json
graph_health_report.md
identity_registry.json
identity_report.md
institutional_audit_report.json
institutional_audit_report.md
institutional_fitness_report.json
institutional_fitness_report.md
knowledge_health_report.json
knowledge_health_report.md
knowledge_index_report.md
life_history_report.json
life_history_report.md
playbook_report.json
playbook_report.md
reality_alignment_report.json
skill_report.json
skill_report.md
trust_registry.json
trust_report.json
trust_report.md
v09_release_report.json
v09_release_report.md
verification_report.json
verification_report.md
```

Notes:

- The `*-report` subcommands in `scripts/hermes.py` emit the `.md` form by default and `.json` when `--json` is passed. Several commands (`roi-report`, `strategy-report`) write both files in a single run.
- `failure_learning_report.md` and `knowledge_index_report.md` are produced by their respective subcommands; presence on disk depends on whether the operator has run `failure-report` or `knowledge-index-report`.
- Registry files (`belief_registry.json`, `trust_registry.json`, `evidence_registry.json`, `identity_registry.json`, `deliberation_skill_registry.json`) are SSOT artifacts maintained by their owning kernels; report generators read them but do not overwrite them.
