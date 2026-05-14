"""
Evolution Audit Logger — Immutable audit trail for all evolution activities.

Records every significant evolution event:
  - Proposals created
  - Simulations run
  - Approvals granted
  - Rejections issued
  - Rollbacks executed

All entries are immutable once written and persisted to:
  observability/evolution_audit/audit_YYYY-MM-DD.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
EVOLUTION_AUDIT_DIR = AMBIENT_ROOT / "observability" / "evolution_audit"


class AuditAction:
    """Standard evolution audit actions."""
    PROPOSAL_CREATED = "proposal_created"
    SIMULATION_RUN = "simulation_run"
    BENCHMARK_RUN = "benchmark_run"
    APPROVAL_GRANTED = "approval_granted"
    REJECTION_ISSUED = "rejection_issued"
    ROLLBACK_EXECUTED = "rollback_executed"
    REVIEW_REQUESTED = "review_requested"


@dataclass
class EvolutionAuditEntry:
    """A single immutable audit log entry."""
    entry_id: str = field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    proposal_id: str = ""
    action: str = ""
    actor: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "entry_id": self.entry_id,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "proposal_id": self.proposal_id,
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
        }


class EvolutionAuditLogger:
    """
    Audit logging for all evolution activities.

    Provides an immutable audit trail for every evolution proposal,
    simulation, approval, rejection, and rollback. Ensures full
    traceability of all system evolution decisions.

    Usage:
        audit = EvolutionAuditLogger()

        audit.log_proposal(proposal)
        audit.log_simulation(simulation_result)
        audit.log_approval("patch_001", approver="admin", rationale="Low risk, clear benefit")
        audit.log_rejection("patch_002", rejector="admin", rationale="Too risky")

        trail = audit.get_audit_trail("patch_001")
    """

    def __init__(self, persist: bool = True, max_entries: int = 5000):
        self._entries: list[EvolutionAuditEntry] = []
        self._max_entries = max_entries
        self._persist = persist

        if persist:
            EVOLUTION_AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    def log_proposal(self, proposal: Any) -> EvolutionAuditEntry:
        """
        Log a new evolution proposal.

        Args:
            proposal: PatchProposal or dict with patch_id, title, type, risk_score
        """
        if hasattr(proposal, "to_dict"):
            proposal_data = proposal.to_dict()
        elif isinstance(proposal, dict):
            proposal_data = proposal
        else:
            proposal_data = {"raw": str(proposal)}

        proposal_id = proposal_data.get("patch_id", "unknown")

        entry = EvolutionAuditEntry(
            proposal_id=proposal_id,
            action=AuditAction.PROPOSAL_CREATED,
            actor="evolution_engine",
            details={
                "title": proposal_data.get("title", ""),
                "type": proposal_data.get("type", ""),
                "target_module": proposal_data.get("target_module", ""),
                "risk_score": proposal_data.get("risk_score", 0.0),
            },
        )

        self._append_entry(entry)
        logger.info("Audit: proposal created — %s", proposal_id)
        return entry

    def log_simulation(self, simulation_result: Any) -> EvolutionAuditEntry:
        """
        Log a simulation run.

        Args:
            simulation_result: SimulationResult or dict with simulation details
        """
        if hasattr(simulation_result, "to_dict"):
            sim_data = simulation_result.to_dict()
        elif isinstance(simulation_result, dict):
            sim_data = simulation_result
        else:
            sim_data = {"raw": str(simulation_result)}

        entry = EvolutionAuditEntry(
            proposal_id=sim_data.get("simulation_id", "unknown"),
            action=AuditAction.SIMULATION_RUN,
            actor="evolution_engine",
            details={
                "changes_applied": len(sim_data.get("changes_applied", [])),
                "broken_dependencies": len(sim_data.get("broken_dependencies", [])),
                "risk_areas": len(sim_data.get("risk_areas", [])),
                "health_score_delta": sim_data.get("health_score_delta", 0.0),
            },
        )

        self._append_entry(entry)
        logger.info("Audit: simulation run — %s", entry.proposal_id)
        return entry

    def log_approval(
        self,
        proposal_id: str,
        approver: str,
        rationale: str = "",
        conditions: list[str] | None = None,
    ) -> EvolutionAuditEntry:
        """
        Log a governance approval for a proposal.

        Args:
            proposal_id: ID of the approved proposal
            approver: Who approved it
            rationale: Why it was approved
            conditions: Any conditions attached to the approval
        """
        entry = EvolutionAuditEntry(
            proposal_id=proposal_id,
            action=AuditAction.APPROVAL_GRANTED,
            actor=approver,
            details={
                "rationale": rationale,
                "conditions": conditions or [],
            },
        )

        self._append_entry(entry)
        logger.info("Audit: approval granted — %s by %s", proposal_id, approver)
        return entry

    def log_rejection(
        self,
        proposal_id: str,
        rejector: str,
        rationale: str = "",
    ) -> EvolutionAuditEntry:
        """
        Log a governance rejection for a proposal.

        Args:
            proposal_id: ID of the rejected proposal
            rejector: Who rejected it
            rationale: Why it was rejected
        """
        entry = EvolutionAuditEntry(
            proposal_id=proposal_id,
            action=AuditAction.REJECTION_ISSUED,
            actor=rejector,
            details={"rationale": rationale},
        )

        self._append_entry(entry)
        logger.info("Audit: rejection issued — %s by %s", proposal_id, rejector)
        return entry

    def log_rollback(
        self,
        proposal_id: str,
        reason: str = "",
        triggered_by: str = "system",
    ) -> EvolutionAuditEntry:
        """
        Log a rollback event.

        Args:
            proposal_id: ID of the proposal being rolled back
            reason: Why the rollback was triggered
            triggered_by: Who/what triggered the rollback
        """
        entry = EvolutionAuditEntry(
            proposal_id=proposal_id,
            action=AuditAction.ROLLBACK_EXECUTED,
            actor=triggered_by,
            details={"reason": reason},
        )

        self._append_entry(entry)
        logger.info("Audit: rollback executed — %s reason=%s", proposal_id, reason)
        return entry

    def get_audit_trail(self, proposal_id: str) -> list[dict[str, Any]]:
        """
        Get the full audit trail for a specific proposal.

        Args:
            proposal_id: The proposal ID to query

        Returns:
            List of audit entries in chronological order
        """
        trail = [
            e.to_dict() for e in self._entries
            if e.proposal_id == proposal_id
        ]
        trail.sort(key=lambda x: x["timestamp"])
        return trail

    def get_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get the most recent audit entries."""
        return [e.to_dict() for e in self._entries[-limit:]]

    def stats(self) -> dict[str, Any]:
        """Get aggregate audit statistics."""
        if not self._entries:
            return {"total_entries": 0, "by_action": {}, "unique_proposals": 0}

        by_action: dict[str, int] = {}
        proposals: set[str] = set()

        for entry in self._entries:
            by_action[entry.action] = by_action.get(entry.action, 0) + 1
            proposals.add(entry.proposal_id)

        return {
            "total_entries": len(self._entries),
            "by_action": by_action,
            "unique_proposals": len(proposals),
        }

    def _append_entry(self, entry: EvolutionAuditEntry) -> None:
        """Append an entry to the audit log."""
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

        if self._persist:
            self._persist_entry(entry)

    def _persist_entry(self, entry: EvolutionAuditEntry) -> None:
        """Persist audit entry to daily JSONL file."""
        try:
            date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            filepath = EVOLUTION_AUDIT_DIR / f"audit_{date_str}.jsonl"
            with filepath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            logger.warning("Failed to persist evolution audit entry %s", entry.entry_id)
