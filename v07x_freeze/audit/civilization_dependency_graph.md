# Civilization Dependency Graph — v070–v077

## Score inheritance chain

```mermaid
flowchart TD
    v065c[ExternalRuntimeGovernanceScore v065c]
    v070[CognitiveCivilizationStabilityScore v070]
    v071[CognitiveRealityAlignmentScore v071]
    v072[CognitiveTemporalContinuityScore v072]
    v073[CognitiveMeaningContinuityScore v073]
    v074[CognitiveValueContinuityScore v074]
    v075[CognitiveIntentContinuityScore v075]
    v076[CognitivePurposeBoundaryScore v076]
    v077[CognitiveAgencyBoundaryScore v077]
    freeze[CivilizationLineageIntegrityScore freeze]

    v065c --> v070
    v070 --> v071
    v071 --> v072
    v072 --> v073
    v073 --> v074
    v074 --> v075
    v075 --> v076
    v076 --> v077
    v070 --> freeze
    v071 --> freeze
    v072 --> freeze
    v073 --> freeze
    v074 --> freeze
    v075 --> freeze
    v076 --> freeze
    v077 --> freeze
```

## Governor attachment order

```mermaid
flowchart LR
    ext[External advisory hints]
    rt[runtime_external_observability]
    civ[civilization_observability]
    real[reality_alignment_observability]
    temp[temporal_continuity_observability]
    sem[semantic_continuity_observability]
    val[value_continuity_observability]
    int[intent_continuity_observability]
    pur[purpose_boundary_observability]
    ag[agency_boundary_observability]

    ext --> rt --> civ --> real --> temp --> sem --> val --> int --> pur --> ag
```

## Module dependencies (governance)

| Child | Depends on |
|-------|------------|
| v071 reality | v070 civilization anchor patterns |
| v072 temporal | v071 reality alignment report |
| v073 meaning | v072 temporal continuity report |
| v074 value | v073 meaning continuity report |
| v075 intent | v074 value continuity report |
| v076 purpose | v075 intent continuity report |
| v077 agency | v076 purpose boundary report |

Each observability package imports the parent score evaluator and applies a layer-specific metric bonus (weights ~0.021–0.024 per dimension).
