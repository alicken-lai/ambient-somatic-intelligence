# Advisory Integrity Report — v07x Observability

**Audit date:** 2026-05-20

## advisory_only flag

All civilization-lineage observability factories set `advisory_only=True`:

- `governance/civilization/civilization_observability.py`
- `governance/reality/reality_alignment_observability.py`
- `governance/temporal/temporal_continuity_observability.py`
- `governance/meaning/semantic_continuity_observability.py`
- `governance/value/value_continuity_observability.py`
- `governance/intent/intent_continuity_observability.py`
- `governance/purpose/purpose_boundary_observability.py`
- `governance/agency/agency_boundary_observability.py`
- `governance/external/runtime/runtime_external_observability.py`

## Runtime test evidence

`tests/v070/test_governor_civilization_wiring.py::test_governor_attaches_civilization_observability` asserts:

- `civilization_observability["advisory_only"] is True`
- `accepted` unchanged after attachment

Parallel governor wiring tests exist for v071–v077.

## No override paths found

- No v07x code writes to `decision.accepted` inside `_attach_*_observability`
- No v07x code modifies `governed_salience` after coherence/homeostasis in attachment chain
- External skill hints remain read-only (`ExternalSkillRegistry.advisory_for_route`)

**Advisory integrity: PASS**
