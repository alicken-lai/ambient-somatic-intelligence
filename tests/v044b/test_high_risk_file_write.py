"""Phase 1 — high-risk GuardedFileWriter paths."""

from __future__ import annotations

import pytest

from governance.audit_log import GovernanceAuditLog
from governance.policy_engine import RiskLevel
from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.guarded_file_writer import GuardedFileWriter
from kernel.isolation.write_target import WriteTarget


def test_governance_audit_governed_append(
    governed_context: ExecutionContext,
    guarded_writer: GuardedFileWriter,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("AMBIENT_OS_ROOT", str(tmp_path))
    audit_dir = tmp_path / "governance" / "audit"
    log = GovernanceAuditLog(audit_dir=audit_dir, guarded_writer=guarded_writer)
    log.record_decision(
        action="test",
        risk=RiskLevel.ALLOW,
        reason="v044b",
        execution_context=governed_context,
    )
    assert (tmp_path / "governance" / "audit" / "decisions.jsonl").exists()


def test_guarded_writer_denies_without_context(guarded_writer: GuardedFileWriter):
    with pytest.raises(PermissionError):
        guarded_writer.append_jsonl(
            "governance/audit/decisions.jsonl",
            {"x": 1},
            target=WriteTarget.GOVERNANCE_AUDIT,
            context=None,
        )
