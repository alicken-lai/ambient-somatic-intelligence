# Recall Evidence Contract

Phase: 1B Memory Event Schema and Recall Evidence Contract  
Date: 2026-06-09  
Status: Contract only. No recall implementation is changed by this document.

## Purpose

Every recall operation must produce an auditable evidence packet. The packet must explain what was queried, which records were candidates, how they were ranked, what was excluded, which backend produced candidates, and whether any action was authorized.

The JSON Schema lives at `schemas/recall_evidence.schema.json`.

## Non-Negotiable Rules

1. Recall is evidence, not truth.
2. Vector recall is candidate recall only.
3. Recall does not authorize decisions.
4. Recall does not authorize actions.
5. Guardian must be able to inspect the packet.
6. Replay must be able to reconstruct the query, candidates, scores, filters, backend, timestamp, and initiating agent.

## Required Defaults

| Field | Default |
| --- | --- |
| `guardian_visible` | `true` |
| `decision_allowed` | `false` |
| `action_allowed` | `false` |
| `no_decision_made` | `true` |

These defaults preserve the boundary that candidate recall cannot become autonomous action.

## Required Packet Fields

| Field | Meaning |
| --- | --- |
| `recall_id` | Stable id for this recall operation. |
| `timestamp` | Recall operation timestamp. |
| `query_type` | Query class, such as text, sensor, event, record_id, or replay. |
| `query_summary` | Safe summary of the query. |
| `query_hash` | Hash of canonical query payload. |
| `initiating_agent` | Agent or actor that initiated recall. |
| `source_node` | Node where recall occurred. |
| `vector_backend` | Backend used for vector candidates, or `none`. |
| `embedding_model` | Embedding model used for vector query, or `none`. |
| `candidate_record_ids` | Candidate memory record ids returned. |
| `similarity_scores` | Similarity scores aligned with candidate ids. |
| `ranking_method` | Ranking method applied after candidate generation. |
| `filters_applied` | General filters. |
| `privacy_filters_applied` | Privacy filters used before or during ranking. |
| `governance_filters_applied` | Governance filters used before or during ranking. |
| `excluded_records` | Records excluded and reasons. |
| `provenance` | Backend, source, index, and record provenance. |
| `confidence` | Overall confidence in recall quality. |
| `guardian_visible` | Whether Guardian can inspect the packet. |
| `decision_allowed` | Whether the recall authorized a decision. Must default false. |
| `action_allowed` | Whether the recall authorized action. Must default false. |
| `replay_reference` | Replay pointer for reconstructing recall. |
| `no_decision_made` | Must default true for candidate recall. |

## Guardian Inspection Requirements

Guardian must be able to inspect:

- Why a memory was recalled.
- Where it came from.
- What backend produced it.
- What ranking method was applied.
- What filters were applied.
- Whether privacy filters were applied.
- Whether governance filters were applied.
- Whether excluded records existed.
- Whether a decision or action was allowed.
- Whether the packet explicitly asserts `no_decision_made`.

## Replay Reconstruction Requirements

Replay must be able to reconstruct:

- Query summary and query hash.
- Initiating agent.
- Source node.
- Candidate record ids.
- Similarity scores.
- Ranking method.
- Filters and exclusions.
- Vector backend or non-vector backend.
- Embedding model or `none`.
- Recall timestamp.
- Replay reference.

## Backend Neutrality

The contract supports any backend. `vector_backend` may be `none`, `lexical`, `inverted_index`, `memory_kernel`, `turbovec`, or another reviewed backend label.

TurboVec is only a possible backend value. It is not the default backend.

