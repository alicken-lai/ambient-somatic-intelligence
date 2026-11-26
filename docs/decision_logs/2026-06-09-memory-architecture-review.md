# 2026-06-09 Memory Architecture Review

## Findings

ASI has a real layered memory architecture with append-only DMN memory, classified memory layers, agent-local memory, ontology promotion rules, replay catalogs, Guardian logs, and trace schemas.

The architecture is ready for a design-only TurboVec placement decision but not ready for TurboVec implementation.

TurboVec should sit as an optional candidate recall backend between durable memory records and governed recall ranking. It must return source-linked candidate evidence and must not modify DMN, promote memory, trigger Guardian actions, alter replay gates, or become a source of truth.

## Risks

- Memory schemas are too thin for vector-backed provenance.
- Recall paths are split across scripts, kernel, index, agent memory, and MCP-facing tools.
- Recalled memories do not consistently include replay pointers.
- Guardian cannot yet inspect a standardized recall evidence packet.
- Cross-node synchronization is policy-only and should not be assumed.
- Historical encoding corruption exists in some memory records and can degrade embedding quality.

## Readiness Score

Overall score: 17 / 30

| Category | Score |
| --- | ---: |
| Architecture | 3 / 5 |
| Memory Schema | 2 / 5 |
| Replay Compatibility | 3 / 5 |
| Guardian Compatibility | 3 / 5 |
| Governance Compatibility | 4 / 5 |
| Synchronization Compatibility | 2 / 5 |

## Recommended Next Phase

Phase 1B: Memory Event Schema and Recall Evidence Contract.

Recommended deliverables:

- ASI memory event schema.
- Recall evidence packet schema.
- Stable record id strategy.
- Replay pointer strategy.
- Embedding sidecar metadata policy.
- Guardian recall evidence review boundary.
- Stale index and encoding-quality screening policy.

Do not implement TurboVec, adapters, dependencies, or production behavior until Phase 1B is complete and reviewed.

## Approval

User requested Phase 1A Memory Architecture Design Review on 2026-06-09. Guardian classification for documentation-only review artifact creation returned `ALLOW` with boundary level `OBSERVE_ONLY`.

