# Governor Wiring Audit — CognitiveGovernor

**Source:** `governance/cognition/cognitive_governor.py`  
**Audit date:** 2026-05-20

## Attachment chain (post-metacognition / homeostasis)

`_attach_external_advisory()` invokes:

1. `_attach_runtime_observability` → `runtime_external_observability`
2. `_attach_civilization_observability` → chains:
   - `civilization_observability`
   - `reality_alignment_observability`
   - `temporal_continuity_observability`
   - `semantic_continuity_observability`
   - `value_continuity_observability`
   - `intent_continuity_observability`
   - `purpose_boundary_observability`
   - `agency_boundary_observability`

## Required ordering vs implementation

| Expected | Implemented | Status |
|----------|-------------|--------|
| runtime_external | First in advisory chain | PASS |
| civilization | Before reality | PASS |
| reality | Before temporal | PASS |
| temporal | Before semantic | PASS |
| semantic | Before value | PASS |
| value | Before intent | PASS |
| intent | Before purpose | PASS |
| purpose | Before agency | PASS |

## Salience / acceptance mutation

Observability `_attach_*` methods reconstruct `GovernanceDecision` copying `accepted` and `governed_salience` unchanged. Docstrings state "never overrides acceptance or salience."

`govern_target()` mutates salience only via constitution, identity, arbitration, and coherence — **before** observability attachment.

## Test coverage

Dedicated wiring tests exist per layer: `tests/v070/test_governor_civilization_wiring.py` through `tests/v077/test_governor_agency_wiring.py`.

**Governor wiring audit: PASS**
