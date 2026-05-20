"""Area 5 — Callback authority."""

from __future__ import annotations

from kernel.isolation.callback_guard import CallbackGuard
from kernel.isolation.callback_scope import CallbackScope, ContextInheritance


def test_register_and_invoke_callback() -> None:
    guard = CallbackGuard()
    scope = CallbackScope(source="bus.test", allowed_writes=frozenset({"state"}))

    def handler(event, data):
        return event

    wrapped = guard.wrap("bus.test", handler, callback_scope=scope)
    assert guard._registry["bus.test"].scope.source == "bus.test"
    assert wrapped("stage", {}) == "stage"


def test_integration_bus_guarded_callback() -> None:
    from kernel.integration_bus import IntegrationBus

    class _Kernel:
        pass

    bus = IntegrationBus(_Kernel())  # type: ignore[arg-type]
    fn = lambda e, d: None
    wrapped = bus.register_guarded_callback("test_hook", fn, source="test")
    assert callable(wrapped)
