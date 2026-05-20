"""Phase 7 — authority trace guarded operations."""

from __future__ import annotations

from observability.v04.authority_trace import AuthorityTrace


def test_record_guarded_operation_fields():
    trace = AuthorityTrace()
    trace.record_guarded_operation(
        mutation_type="FILE_WRITE",
        target="memory",
        context_id="ctx-1",
        caller_id="agent-1",
        rollback_type="snapshot",
        result="allow",
    )
    recent = trace.recent(1)[0]
    assert recent["mutation_type"] == "FILE_WRITE"
    assert recent["caller_id"] == "agent-1"
    assert recent["rollback_type"] == "snapshot"
    assert recent["result"] == "allow"
