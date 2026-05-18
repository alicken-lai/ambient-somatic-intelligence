# Callback Authority Report (v0.4.3)

**Generated:** 2026-05-18T13:24:34.576860+00:00

## Summary

Total callback hooks found: **12**

## Integration Bus Hotspots

- `kernel/integration_bus.py:265` — `on_event`
- `kernel/integration_bus.py:406` — `on_event`
- `kernel/integration_bus.py:433` — `on_event`
- `kernel/integration_bus.py:520` — `subscribe`
- `kernel/integration_bus.py:549` — `subscribe`
- `kernel/integration_bus.py:828` — `on_event`
- `kernel/integration_bus.py:896` — `on_event`
- `kernel/integration_bus.py:994` — `subscribe`
- `somatic/signal_bus.py:94` — `on_hook`
- `somatic/signal_bus.py:95` — `on_hook`

## Risk

Callbacks without `CallbackGuard` registration inherit ambient authority.
