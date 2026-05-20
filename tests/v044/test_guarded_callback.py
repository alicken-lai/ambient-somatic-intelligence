"""Phase 3 — GuardedCallback."""

from __future__ import annotations

from kernel.isolation.guarded_callback import GuardedCallback
from observability.v04.authority_trace import AuthorityTrace


def test_guarded_callback_wraps_handler():
    trace = AuthorityTrace()
    gc = GuardedCallback(authority_trace=trace)
    seen = []

    def handler(x: int) -> int:
        seen.append(x)
        return x * 2

    wrapped = gc.register("unit_hook", handler, source="test")
    assert wrapped(3) == 6
    assert seen == [3]
    events = trace.recent(5)
    assert any(e.get("mutation_type") == "CALLBACK_MUTATION" for e in events)
