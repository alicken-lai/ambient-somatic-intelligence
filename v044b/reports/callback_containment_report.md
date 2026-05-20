# Callback High-Risk Containment (v0.4.4B Phase 5)

## IntegrationBus

`register_guarded_callback()` now routes through `GuardedCallback` with:

- High-risk source detection (`governance`, `memory`, `truth`, `telemetry`, `replay`, `integration`)
- `ContextInheritance.ISOLATE` for high-risk sources
- Authority trace on registration

## Somatic (baseline)

`somatic/signal_bus.py` retains v0.4.4 `GuardedCallback` integration.

## Constraint

Callbacks must not mutate governance/memory/truth/release without inherited or supplied `ExecutionContext` on governed registration paths.
