# Inter-Sovereign Boundary Matrix (v0.7.0)

| From \\ To | Ambient | Hermes | Foreign (advisory) |
|------------|---------|--------|---------------------|
| **Ambient** | — | orchestration | advisory_interop |
| **Hermes** | client | — | read_only hints |
| **Foreign** | non-coercive hints | no override | peer advisory |

## Boundary rules

1. **Non-interference:** foreign payloads must not force `accepted` or salience overrides.
2. **Sandbox:** `cognition_sandbox_boundary.py` contains code/exec escape attempts.
3. **Provenance:** `provenance_exchange.py` requires `source` + `route_name`; forbids `merge_identity`.
4. **Governor wiring:** `civilization_observability` attached after runtime soak — never mutates decisions.

## Gate

`CognitiveCivilizationStabilityScore >= 0.90` (see `observability/v070/`).
