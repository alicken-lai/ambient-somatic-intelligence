# Kernel Dependency Audit

## Scope

This audit reviews Hermes-ASI v0.9 kernels as an integrated institutional intelligence system. It is descriptive only and does not change runtime behavior or governance.

## Kernel Matrix

| Kernel | Inputs | Outputs | Dependencies | Consumers |
| --- | --- | --- | --- | --- |
| Deliberation | task prompt, mode, provider context | trace, final answer, child outputs | provider registry, routing config | evaluation, verification, reports |
| Evaluation | golden traces, deliberation traces | quality, learning, ROI reports | deliberation trace schema | routing, skills, strategy memory |
| Routing | provider registry, routing rules, policy flags | provider choice, audit metadata | orchestration models, health checker | deliberation, CLI route |
| Skills | benchmark results, task classes | skill registry, skill reports | evaluation A/B results | playbooks, identity, reality alignment |
| Verification | knowledge artifacts, playbooks | claims, evidence statuses, contradiction reports | claims/evidence registries | acquisition, calibration, reality alignment |
| Acquisition | verification artifacts, source registry | candidate evidence, quality metrics, knowledge index | verification pipeline | calibration, knowledge health |
| Calibration | acquisition assets, trust registry | trust, confidence, drift, knowledge health | acquisition reports, trust models | reality alignment, identity |
| Reality Alignment | trust records, skills, playbooks, belief registry | reality score, diversity, challenge, fitness reports | calibration, knowledge assets | identity, audit report |
| Identity | belief registry, reality reports, DMN summaries | identity, continuity, life-history reports | reality alignment, DMN, trust/drift reports | audit report, README narrative |

## Findings

- The kernels form a mostly linear institutional pipeline: deliberation -> verification -> acquisition -> calibration -> reality alignment -> identity.
- Routing/orchestration sits beside the pipeline and controls provider selection rather than belief or identity state.
- Knowledge graph integration is cumulative: skills/playbooks, acquisition, calibration, reality, and identity each add edges.
- Reports are the main integration surface between phases. This is clear and auditable but creates generated-artifact churn.

## Dead Paths

- No hard dead code was found in the core Phase 1-9 path.
- External validation in Phase 8 is intentionally a stub. It is not dead; it is a safety placeholder.
- Identity evolution accepts change records for review but does not apply them. This matches "no silent evolution."

## Duplicate Responsibilities

- "Confidence" appears in verification, acquisition, calibration, reality alignment, and identity. Meanings differ by layer and should remain documented.
- "Health" appears as knowledge health and identity health. They should not be merged.
- Reports and registries are both stored in `reports/`, making runtime-vs-evidence distinction less obvious.

## Missing Links

- DMN write integration is not automatic for every kernel report; current memory logging is operator/tool driven.
- No single manifest maps report artifacts to their generating command.
- Knowledge graph coverage is present but not automatically materialized into a persistent graph report.

## Tight Coupling

- Calibration calls acquisition builders, which call verification builders. This is convenient but causes report-generation side effects and registry timestamp churn.
- Reality alignment builds targets from calibration and knowledge assets, so running identity reports can indirectly refresh lower-layer registries.

## Recommendation

Keep the kernel chain but introduce a read-only snapshot interface for audit/report generation. This would reduce registry churn while preserving the current advisory boundaries.
