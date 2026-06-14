# DMN Conflict Resolution Policy

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Policy only. No DMN behavior is changed by this document.

## Purpose

DMN memory must be able to hold contradictory records without pretending that one record automatically wins.

Newer is not always better. More frequent is not always true. Vector-nearer is not authoritative.

## Existing Conflict Evidence

The repository already contains conflict-aware governance modules:

- `governance/reality/truth_conflict_analysis.py` detects divergence and supports plural realities without forced merge.
- `governance/temporal/continuity_conflict.py` detects forced continuity sync and epoch merge conflicts.
- Related value, meaning, intent, purpose, and agency modules reject universal or forced synchronization.
- `memory/ontology/promotion_chain_validator.py` blocks promotion when active contradictions exist.
- `memory/ontology/decay_engine.py` applies contradiction penalties.

The gap is that these are domain modules, not yet a unified DMN conflict workflow.

## Conflict Types

| Type | Example | Default Handling |
| --- | --- | --- |
| Factual conflict | Two records report incompatible state. | Preserve both; lower confidence until reviewed. |
| Temporal conflict | Records from different epochs describe different conditions. | Preserve epoch lineage; do not merge epochs. |
| Source conflict | Home Hermes and Office Hermes report different observations. | Preserve source node and context. |
| Governance conflict | A new policy conflicts with old doctrine. | Mark old policy superseded only after review. |
| Sensor conflict | Sensor readings disagree. | Preserve modality, calibration, and source confidence. |
| Interpretation conflict | Same evidence yields different conclusions. | Preserve alternatives and rationale. |

## Resolution Strategies

| Strategy | Use | Benefit | Risk |
| --- | --- | --- | --- |
| Confidence weighting | When confidence models and evidence quality are available. | Keeps ranking explainable. | Can over-trust flawed confidence scores. |
| Source weighting | When sources have known reliability or authority. | Handles node or sensor trust differences. | Can bias against rare but correct sources. |
| Coexistence | When conflict is unresolved or context-dependent. | Avoids false certainty. | Recall must clearly show conflict state. |
| Human review | For high-impact ambiguity or operator preference. | Provides explicit accountability. | Slower and not scalable alone. |
| Guardian review | For safety, governance, external action, or policy-sensitive conflict. | Preserves safety boundaries. | Guardian must inspect provenance, not only content. |
| Supersession | When an old policy is replaced through governance. | Keeps history while clarifying active policy. | Unsafe if used as silent deletion. |

## Conflict Rules

1. Contradictory records may coexist.
2. Unresolved conflicts block promotion into higher layers.
3. Governance-impacting conflicts require human or Guardian review.
4. Conflict resolution must preserve the losing or superseded record as history unless higher policy requires deletion.
5. Recall must expose conflict status when a returned record is disputed.
6. Cross-node conflicts must preserve node identity and sync manifest references.
7. Vector similarity must never resolve conflict by itself.

## Required Conflict Metadata

Future conflict records should include:

- `conflict_id`
- `record_ids`
- `conflict_type`
- `detected_at`
- `detected_by`
- `source_nodes`
- `summary`
- `evidence_refs`
- `confidence_delta`
- `resolution_state`
- `reviewer_id`
- `guardian_review_id`
- `decision_log_ref`
- `rollback_or_supersession_ref`

## Resolution States

Allowed states:

- `unresolved`
- `coexisting`
- `under_review`
- `resolved_by_confidence`
- `resolved_by_source`
- `resolved_by_human`
- `resolved_by_guardian`
- `superseded`
- `tombstoned`

Unresolved and under-review conflicts must remain visible to recall and promotion gates.
