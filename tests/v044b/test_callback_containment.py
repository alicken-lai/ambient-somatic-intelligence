"""Phase 5 — high-risk callback containment."""

from __future__ import annotations

from kernel.isolation.guarded_callback import GuardedCallback
from observability.v04.authority_trace import AuthorityTrace


def test_guarded_callback_registers_with_trace():
    trace = AuthorityTrace()
    gc = GuardedCallback(authority_trace=trace)

    def hook(_payload):
        return None

    wrapped = gc.register("governance_hook", hook, source="governance")
    assert callable(wrapped)
    events = trace.recent(limit=5)
    assert any(e.get("mutation_type") == "CALLBACK_MUTATION" for e in events)
