# Governance Layer Matrix — v070–v077

**Base:** v0.7.7-alpha BOUNDED CIVILIZATION AGENCY GOVERNANCE

## Lineage stack (advisory-only)

| Layer | Version | Governance package | Primary score module | Gate threshold | Governor observability field |
|-------|---------|-------------------|----------------------|----------------|---------------------------|
| Civilization | v070 | `governance/civilization/` | `cognitive_civilization_stability_score` | 0.90 | `civilization_observability` |
| Reality alignment | v071 | `governance/reality/` | `cognitive_reality_alignment_score` | 0.90 | `reality_alignment_observability` |
| Temporal continuity | v072 | `governance/temporal/` | `cognitive_temporal_continuity_score` | 0.90 | `temporal_continuity_observability` |
| Meaning continuity | v073 | `governance/meaning/` | `cognitive_meaning_continuity_score` | 0.90 | `semantic_continuity_observability` |
| Value continuity | v074 | `governance/value/` | `cognitive_value_continuity_score` | 0.90 | `value_continuity_observability` |
| Intent continuity | v075 | `governance/intent/` | `cognitive_intent_continuity_score` | 0.90 | `intent_continuity_observability` |
| Purpose boundary | v076 | `governance/purpose/` | `cognitive_purpose_boundary_score` | 0.90 | `purpose_boundary_observability` |
| Agency boundary | v077 | `governance/agency/` | `cognitive_agency_boundary_score` | 0.90 | `agency_boundary_observability` |

## Underlying cognition stack (unchanged)

| Layer | Version | Role in v07x |
|-------|---------|--------------|
| Cognitive governance | v060 | Arbitration engine, sovereignty limits |
| Constitutional | v061 | Pre-arbitration block |
| Identity | v062 | Provenance + authority multiplier |
| Coherence | v063 | Post-governance damp / reject |
| Metacognition | v064 | Reflective observability |
| Homeostasis | v065 | Stabilization recommendations |
| External skills | v065b | Read-only hints |
| Runtime soak | v065c | `runtime_external_observability` |

## Integrity properties (verified)

- All v07x observability payloads expose `advisory_only: true`
- No v07x layer mutates `accepted` or `governed_salience` after attachment
- Guardian and constitutional paths precede civilization lineage attachment
- Each layer inherits prior layer score in combined formula (0.86 chain weight)
