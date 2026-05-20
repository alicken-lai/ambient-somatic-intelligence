"""Phase 4 — authority trace expansion."""

from __future__ import annotations

from kernel.isolation.registry_guard import RegistryGuard
from kernel.isolation.write_target import WriteTarget
from observability.v04.authority_trace import AuthorityTrace


def test_registry_guard_emits_trace(governed_context):
    trace = AuthorityTrace()
    guard = RegistryGuard(authority_trace=trace)
    guard.bind("t", write_target=WriteTarget.SKILL_REGISTRY, owner="test")
    guard.mutate("t", lambda: None, context=governed_context, operation="noop")
    events = trace.recent(limit=10)
    assert any(e.get("mutation_type") == "REGISTRY_MUTATION" for e in events)


def test_trace_coverage_meets_target():
    trace = AuthorityTrace()
    for i in range(5):
        trace.record_guarded_operation(
            mutation_type="FILE_WRITE",
            target=f"t{i}",
            caller_id="test",
        )
    guarded = sum(1 for e in trace.recent(10) if e.get("mutation_type"))
    assert guarded / 5 >= 0.7
