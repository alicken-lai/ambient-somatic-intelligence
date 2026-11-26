# DMN Decay Policy

Phase: 1G.5 DMN Memory Governance Review  
Date: 2026-06-09  
Status: Policy only. No DMN behavior is changed by this document.

## Purpose

Decay controls how memory loses retrieval priority, requires review, or moves to archive without silently erasing history.

DMN memory is append-only by default. Decay is not deletion. Decay should affect confidence, freshness, recall ranking, archive recommendations, and review requirements.

## Existing Decay Evidence

The repository already contains:

- `memory/ontology/decay_rules.py`: per-layer base rate, inactivity multiplier, contradiction penalty, minimum confidence.
- `memory/ontology/decay_engine.py`: time decay, inactivity decay, contradiction penalty, failed reuse penalty, at-risk reports.
- `memory/memory_kernel.py`: storage-layer TTLs, recall decay half-lives, archive movement, deduplication, access counts, and statistics.

## Retention Classes

| Retention Class | Typical Content | Default Handling |
| --- | --- | --- |
| Ephemeral | Scratchpad, temporary task context, transient sensor noise. | Short TTL; not DMN unless promoted. |
| Episodic | Raw events, logs, sensor episodes, traces. | Retain for replay window; decay quickly for recall. |
| Operational | Procedures, recurring project facts, useful implementation patterns. | Decay on inactivity or failed reuse. |
| Governance | Constitution, policies, Guardian decisions, PR gates, decision logs. | Decay conservatively; archive rather than delete. |
| Replay-Critical | Incidents, failed gates, source evidence, checksums, replay manifests. | Must not be silently deleted; preserve replay pointer. |
| Restricted | Sensitive or high-risk content. | Retain only with policy basis; prefer summaries and tombstones. |

## Freshness

Freshness describes how recently the record was observed, validated, recalled, or reused.

Freshness should include:

- event age
- last accessed time
- last validated time
- last successful reuse
- last contradiction
- last governance review

Freshness can lower recall ranking. It must not hide governance-critical failures.

## Importance Scores

Importance should be independent from freshness.

Recommended factors:

| Factor | Meaning |
| --- | --- |
| Governance impact | Does the memory affect policy, safety, Guardian, review, or escalation? |
| Replay value | Is the memory needed to reconstruct an event or decision? |
| Recurrence | Has the observation repeated across events or contexts? |
| Human confirmation | Did the operator mark it important? |
| Guardian relevance | Did Guardian review, allow, block, or observe it? |
| Operational usefulness | Has it helped complete future work safely? |
| Privacy risk | Does retention increase exposure risk? |

## Archive Thresholds

Archive should be recommended when:

- confidence approaches layer minimum;
- the record is old and rarely accessed;
- operational usefulness is low;
- the record is superseded by a consolidated derived memory;
- raw content is sensitive and a summary can preserve governance value.

Archive must preserve:

- original source reference;
- archive timestamp;
- archive reason;
- lineage;
- replay pointer or replay-unavailable reason;
- privacy class;
- governance state.

## Deletion Restrictions

The following must not be silently deleted:

- governance decisions;
- Guardian observations;
- failed checks;
- replay-critical records;
- promotion, consolidation, conflict, and sync audit records;
- tombstones;
- records involved in unresolved contradictions;
- records required for legal, safety, or project accountability.

When deletion is required by higher policy, create a tombstone unless prohibited.

## Governance Memories Decay Differently

Governance memories should decay by review state, not simple age.

Old governance memory may become stale, but it remains historically important. The correct action is usually:

1. mark as superseded;
2. link to replacement policy;
3. reduce active recall priority;
4. keep archived replay evidence.

Sensor and telemetry memories may decay faster, especially when they are raw, repetitive, low-impact, and not replay-critical.
