# Hermes-ASI v0.9.0-rc1 Known Limitations

> **Release**: Hermes-ASI v0.9.0-rc1
> **Document type**: Known limitations and future work
> **Scope**: All known limitations explicitly acknowledged at the rc1 release point.
> **Companion docs**: `docs/release/GOVERNANCE_LOCK.md`, `docs/release/V09_RELEASE_CHECKLIST.md`, `docs/release/TECH_DEBT_PRIORITY.md`

## 1. Overview

This document lists known limitations and future work for
Hermes-ASI v0.9.0-rc1.

The release is an **advisory institutional intelligence architecture**. It is
not an autonomous governance authority. Kernels do not execute autonomous
corrective action. Every external action requires operator intent plus
Guardian classification.

Limitations are stated here so that downstream phases can decide whether to
treat each gap as accepted debt, schedule a fix in v0.9.x stabilization, or
defer it to a later phase. None of the items below authorize bypassing the
governance lock described in `docs/release/GOVERNANCE_LOCK.md`.

## 2. Legacy DMN Entries

`memory/dmn.jsonl` currently holds 1753 valid events out of 1756 total. The
remaining 3 invalid events are early schema-evolution leftovers. The validator
(`tools/validate_dmn_events.py`) normalizes them at read time but does not
migrate the underlying records.

- **Impact**: recall and replay continue to work via normalization.
- **Risk**: low. The invalid events are read-only artifacts and the gap is
  bounded to 3 records.
- **Future**: governed migration path, or explicit marking of those records as
  `historical` / `superseded`. Migration must follow the append-only repair
  doctrine in `canonical_rules.md` Section 3 and must not silently erase the
  originals.

## 3. External Validation Stubs

`hermes/reality_alignment/external_validation.py` and adjacent modules are
stubs. There is no real external reality source integration. The reality score
is derived from internal knowledge-graph challenges, not from external
fact-checking.

- **Impact**: reality alignment is echo-chamber-aware but cannot independently
  refute a claim against an outside source.
- **Risk**: medium for any strategy that assumes external grounding.
- **Future**: integrate verifiable external reality sources through a governed
  provider path behind Guardian classification.

## 4. Limited External Reality Sources

Reality alignment currently relies on:

- Internal knowledge diversity
- Echo-chamber detection
- Fitness scoring

There is no web-scale fact-checking and no API integration with external
knowledge bases in rc1.

- **Impact**: the system can detect internal contradictions but cannot prove
  correspondence to outside facts.
- **Future**: introduce external knowledge-base adapters behind Guardian.

## 5. Provider Constraints

- All providers communicate through CLI adapters (`hermes/providers/cli_adapter.py`,
  `hermes/providers/cli_discovery.py`, `hermes/providers/base.py`). `route --invoke`
  is gated by Guardian and is the only trigger for actual provider calls.
- Provider availability depends on the local environment (IDE, cloud LLM,
  local model). rc1 does not guarantee any specific provider is present.
- No automated fallback-chain test coverage exists yet.
- The `user-hermes-asi` cross-IDE subagent calling protocol is defined, but
  actual IDE-instance availability is not guaranteed.

- **Impact**: routing may degrade silently if a referenced provider is missing.
- **Future**: provider-capability probe and fallback chain with test coverage.

## 6. Current Graph Assumptions

- `graph_health` is derived from release artifacts (`reports/`, registries),
  not from an independent graph database.
- `node_count = 46` and `edge_count = 47` are freeze-point snapshots.
- `relationship_coverage` is approximately 90 percent; a subset of the expected
  relations are not yet instantiated.
- There is no persistent graph storage.

- **Impact**: graph metrics are reproducible from artifacts but not queryable
  as a live graph.
- **Future**: evaluate `networkx`-backed or dedicated graph-DB storage in a
  later phase.

## 7. Project Layout Constraints

- No `pyproject.toml`, `requirements.txt`, or `setup.py`. The repository uses
  a flat layout.
- No formal `pip install` path. Users install by cloning and running
  `python scripts/hermes.py`.
- Third-party dependencies (`pyyaml`, `jsonschema`) must be installed manually.
  Standard-library dependencies (`argparse`, `pathlib`, `dataclasses`) need no
  installation.
- No formal CI workflow documentation ships with rc1.

- **Impact**: onboarding requires manual environment setup.
- **Future**: introduce packaging (`pyproject.toml`) and CI in a later phase.

## 8. Hardcoded Health Constants

The RC health scores include several constants that are not dynamically
measured:

- `test_health` (100.0) is a constant.
- `report_stability` (82.0) is a constant.
- `maintainability` (78.0) is a constant that reflects known tech debt, not a
  dynamic scan.
- `governance` (0.95) is a constant.
- `knowledge_coverage` (0.90) is a file-existence heuristic (presence of
  `hermes/graph/graph_health.py`).
- `identity_continuity` (0.95) is a constant.

These are not dynamic measurements. They are listed as v0.9.x stabilization
tech debt. See `docs/release/TECH_DEBT_PRIORITY.md`.

- **Impact**: health scores convey intent rather than live state.
- **Future**: replace constants with measured signals and freshness metadata.

## 9. Report Snapshot Mode Gap

A shared report snapshot mode is documented but not fully implemented across
all report generators. Some generators refresh underlying registries while
producing a snapshot, which causes timestamp churn.

This is the only unchecked item in `V09_RELEASE_CHECKLIST.md`.

- **Impact**: report determinism is partial.
- **Future**: enforce the snapshot contract across all generators so that
  snapshot production does not mutate source registries.

## 10. DMN Event Taxonomy

The DMN event taxonomy is not yet formally fixed. The `tags` field on DMN
records is not a strict controlled vocabulary.

- **Impact**: cross-record queries rely on convention rather than schema.
- **Future**: v0.9.x will adopt a consistent taxonomy and validate tags against
  it.

## 11. Autonomy Boundary

- v0.9.0-rc1 is advisory-only. Kernels do not execute autonomous corrective
  action.
- There is no self-healing production state.
- All external action requires operator intent plus Guardian classification.

This is intentional and aligned with the P1 freeze (see
`docs/release/GOVERNANCE_LOCK.md` Section 8). It is listed here so adopters do
not infer autonomy that the architecture does not provide.

## 12. DMN Reflection Cycle

The DMN reflection cycle is a local scheduler composed of
`dmn_tick_loop.py` and `dmn_reflection_cycle.py`. It is not distributed.

- **Impact**: only one node runs the reflection cycle.
- **Future**: cross-node reflection coordination may be added in a later phase,
  gated by the DMN sync policy family.

## 13. Future Work

Tracked in `docs/release/TECH_DEBT_PRIORITY.md`. Two horizons:

### 13.1 v0.9.x stabilization

- Shared snapshot mode across all report generators.
- Formal DMN event taxonomy with controlled vocabulary.
- Graph export to a queryable format.
- Stable report writer that does not mutate source registries.
- Freshness metadata for derived health scores.

### 13.2 Later phases

- External reality source integration.
- CI/CD pipeline.
- Packaging via `pyproject.toml` and a formal install path.
- Persistent graph storage.
- Provider fallback-chain test coverage.
