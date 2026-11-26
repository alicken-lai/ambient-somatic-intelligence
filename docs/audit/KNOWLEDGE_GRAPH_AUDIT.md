# Knowledge Graph Audit

## Expected Coverage

| Node Type | Coverage |
| --- | --- |
| Claims | Present through verification claim graph. |
| Evidence | Present through evidence registry and acquisition links. |
| Trust | Present through calibration graph extension. |
| Beliefs | Present through Phase 8 graph extension. |
| Skills | Present through deliberation knowledge graph. |
| Playbooks | Present through deliberation knowledge graph. |
| Reality Events | Present through challenge events/reality scores. |
| Identity Events | Present through Phase 9 graph extension. |
| Guardian Events | Indirect via DMN and governance docs; no explicit Guardian node set. |
| Continuity Events | Present through identity graph extension. |

## Missing Relationships

- Claim -> Belief promotion relationship is implicit, not explicit.
- Guardian event -> policy/rule relationship is not modeled in the graph.
- Report artifact -> generating command relationship is not modeled.

## Duplicate Nodes

- Sources such as `reports`, `verification_reports`, and report filenames can become separate node labels.
- Skills and playbooks may appear both as registry IDs and belief target IDs.

## Isolated Node Risk

- External validation outcomes are supported but may be isolated until actual providers are registered.
- Identity constraints are connected to identity but not to Guardian policy nodes.

## Recommendation

Add a future graph export report that materializes graph coverage and flags isolated nodes. Do not make graph assertions authoritative without verification.
