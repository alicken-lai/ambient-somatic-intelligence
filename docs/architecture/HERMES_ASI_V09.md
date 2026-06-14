# Hermes-ASI v0.9 Architecture

Hermes-ASI v0.9 is a coherent advisory institutional intelligence system. It is not an autonomous governance authority.

## Kernel Relationships

```mermaid
flowchart TD
    T["Task"] --> D["Deliberation"]
    D --> E["Evaluation"]
    E --> S["Skills / Playbooks"]
    S --> V["Verification"]
    V --> A["Evidence Acquisition"]
    A --> C["Trust Calibration"]
    C --> R["Reality Alignment"]
    R --> B["Belief Registry"]
    B --> I["Identity / Continuity"]
    I --> L["Life History"]
    I --> M["DMN / Audit Memory"]
    G["Guardian / Governance"] -. authority boundary .-> D
    G -. authority boundary .-> V
    G -. authority boundary .-> R
    G -. authority boundary .-> I
```

## Lifecycle

```mermaid
sequenceDiagram
    participant Operator
    participant Deliberation
    participant Verification
    participant Acquisition
    participant Calibration
    participant Reality
    participant Identity
    participant DMN

    Operator->>Deliberation: task / prompt
    Deliberation->>Verification: claims and artifacts
    Verification->>Acquisition: unsupported claims
    Acquisition->>Calibration: evidence quality and sources
    Calibration->>Reality: trust and knowledge health
    Reality->>Identity: beliefs and challenge outcomes
    Identity->>DMN: advisory milestone via approved append path
```

## Governance Boundaries

```mermaid
flowchart LR
    K["Kernels"] --> Q["Analyze / score / recommend"]
    Q --> O["Operator decision"]
    O --> H["Hermes / Guardian gate"]
    H -->|ALLOW| X["External or state-changing action"]
    H -->|REVIEW/BLOCK| N["No action"]
```

Kernels may analyze, describe, score, and recommend. They may not modify Guardian, governance rules, credentials, provider permissions, or approval requirements.

## Identity Integration

Identity consumes belief registry, reality reports, trust/drift reports, and recent DMN summaries. It answers:

- Who has Hermes-ASI been?
- What remains stable?
- What changed?
- Why did it change?
- What does it refuse to become?

## Reality Alignment Integration

Reality alignment challenges high-trust beliefs, not only weak beliefs. It produces reality score, fitness score, diversity score, and echo risk.

## DMN Integration

DMN remains append-only. Kernels do not write DMN automatically. Operator/Hermes-mediated append remains the safe integration path.

## Release Posture

v0.9 is release-candidate ready as an advisory institutional intelligence architecture, with runtime snapshot hygiene identified as the main follow-up.
