# DMN Event Taxonomy

DMN remains append-only. This taxonomy standardizes event categories without changing Guardian, governance, or write permissions.

## Required Fields

- `event_type`: one of the canonical taxonomy values.
- `content`: human-readable event summary.
- `timestamp`: event timestamp.

Recommended fields: `source`, `producer_kernel`, `consumer_kernels`, `retention`, `evidence`, `guardian`, `tags`.

## Event Types

| Event Type | Required Meaning | Optional Fields | Retention | Producers | Consumers |
| --- | --- | --- | --- | --- | --- |
| `SYSTEM_EVENT` | local system, daemon, telemetry, runtime status | `source`, `tags` | short/review | runtime tools | health, identity timeline |
| `DELIBERATION_EVENT` | deliberation trace or decision milestone | `evidence`, `producer_kernel` | long | deliberation | verification, audit |
| `VERIFICATION_EVENT` | claim/evidence verification milestone | `evidence` | long | verification | acquisition, audit |
| `EVIDENCE_EVENT` | evidence acquisition or quality milestone | `evidence` | long | acquisition | calibration |
| `TRUST_EVENT` | trust, confidence, drift, calibration milestone | `evidence` | long | calibration | reality, identity |
| `REALITY_EVENT` | reality score, challenge, fitness, diversity milestone | `evidence` | long | reality alignment | identity, audit |
| `IDENTITY_EVENT` | identity, continuity, life-history milestone | `evidence` | permanent | identity | audit |
| `GUARDIAN_EVENT` | Guardian decision, approval, block, review | `guardian`, `evidence` | permanent | Guardian/Hermes | all governed layers |
| `GOVERNANCE_EVENT` | rules, policy, release, audit governance milestone | `evidence` | permanent | operator/audit | identity, release |
| `FAILURE_EVENT` | failed gate, regression, incident, blocked action | `evidence` | permanent | tests/Guardian/audit | recovery, identity |
| `RECOVERY_EVENT` | remediation, passing replay, restored health | `evidence` | permanent | tests/audit/operator | identity |

## Producer Guidance

Kernels should not write DMN automatically. Events should be appended through existing Guardian-scoped Hermes/operator paths.

## Consumer Guidance

Consumers may summarize and classify DMN events, but may not rewrite DMN history or infer policy authority from report output.
