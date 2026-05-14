"""
Governance Audit Log — Immutable decision record with full trace.

Records every governance decision for:
  - Compliance and accountability
  - Pattern analysis (what gets blocked/reviewed most)
  - Policy tuning (identify false positives/negatives)
  - Incident investigation
  - Memory layer integration (writes to governance memory)

Log format: append-only JSONL at governance/audit/decisions.jsonl
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from governance.policy_engine import RiskLevel


AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
AUDIT_DIR = AMBIENT_ROOT / "governance" / "audit"
DECISIONS_LOG = AUDIT_DIR / "decisions.jsonl"
INCIDENTS_LOG = AUDIT_DIR / "incidents.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GovernanceAuditLog:
    """
    Immutable governance decision log.

    Usage:
        audit = GovernanceAuditLog()
        audit.record_decision(
            action="git push --force",
            risk=RiskLevel.BLOCK,
            reason="Force push to protected branch",
            agent_id="cursor-agent",
            matched_policies=["block_force_push_main"],
        )
        stats = audit.stats(hours=24)
    """

    def __init__(self, audit_dir: Path | None = None):
        self.audit_dir = audit_dir or AUDIT_DIR
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_path = self.audit_dir / "decisions.jsonl"
        self.incidents_path = self.audit_dir / "incidents.jsonl"

    def record_decision(
        self,
        action: str,
        risk: RiskLevel,
        reason: str,
        agent_id: str = "unknown",
        matched_policies: list[str] | None = None,
        validation_stages: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a governance decision."""
        record = {
            "timestamp": utc_now(),
            "action": action[:500],
            "risk": risk.name,
            "reason": reason,
            "agent_id": agent_id,
            "matched_policies": matched_policies or [],
            "validation_stages": validation_stages,
            "metadata": metadata or {},
        }

        self._append(self.decisions_path, record)

        if risk == RiskLevel.BLOCK:
            self._record_incident(record)

        return record

    def record_override(
        self,
        action: str,
        original_risk: RiskLevel,
        override_by: str,
        reason: str,
    ) -> dict[str, Any]:
        """Record when a user overrides a governance decision."""
        record = {
            "timestamp": utc_now(),
            "type": "override",
            "action": action[:500],
            "original_risk": original_risk.name,
            "override_by": override_by,
            "reason": reason,
        }
        self._append(self.decisions_path, record)
        return record

    def _record_incident(self, decision: dict[str, Any]) -> None:
        """Record a BLOCK decision as an incident."""
        incident = {
            "timestamp": decision["timestamp"],
            "type": "blocked_action",
            "action": decision["action"],
            "reason": decision["reason"],
            "agent_id": decision["agent_id"],
            "policies": decision["matched_policies"],
            "resolved": False,
        }
        self._append(self.incidents_path, incident)

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def recent_decisions(self, limit: int = 50, risk_filter: RiskLevel | None = None) -> list[dict[str, Any]]:
        """Get recent decisions, optionally filtered by risk level."""
        if not self.decisions_path.exists():
            return []

        records: list[dict[str, Any]] = []
        with self.decisions_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if risk_filter and record.get("risk") != risk_filter.name:
                        continue
                    records.append(record)
                except json.JSONDecodeError:
                    continue

        return records[-limit:]

    def incidents(self, resolved: bool | None = None) -> list[dict[str, Any]]:
        """Get all incidents, optionally filtered by resolution status."""
        if not self.incidents_path.exists():
            return []

        records: list[dict[str, Any]] = []
        with self.incidents_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if resolved is not None and record.get("resolved") != resolved:
                        continue
                    records.append(record)
                except json.JSONDecodeError:
                    continue

        return records

    def stats(self, hours: int = 24) -> dict[str, Any]:
        """Get governance statistics for a time window."""
        if not self.decisions_path.exists():
            return {"total": 0, "by_risk": {}, "by_agent": {}, "top_policies": []}

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        by_risk: Counter[str] = Counter()
        by_agent: Counter[str] = Counter()
        by_policy: Counter[str] = Counter()
        total = 0

        with self.decisions_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = record.get("timestamp", "")
                if ts < cutoff:
                    continue

                total += 1
                by_risk[record.get("risk", "UNKNOWN")] += 1
                by_agent[record.get("agent_id", "unknown")] += 1
                for p in record.get("matched_policies", []):
                    by_policy[p] += 1

        return {
            "window_hours": hours,
            "total": total,
            "by_risk": dict(by_risk),
            "by_agent": dict(by_agent),
            "top_policies": by_policy.most_common(10),
            "block_rate": by_risk.get("BLOCK", 0) / max(total, 1),
            "review_rate": by_risk.get("REVIEW_REQUIRED", 0) / max(total, 1),
        }

    def policy_effectiveness(self) -> list[dict[str, Any]]:
        """Analyze which policies trigger most often (for tuning)."""
        if not self.decisions_path.exists():
            return []

        policy_stats: dict[str, dict[str, int]] = {}

        with self.decisions_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                for p in record.get("matched_policies", []):
                    if p not in policy_stats:
                        policy_stats[p] = {"triggers": 0, "blocks": 0, "reviews": 0, "overrides": 0}
                    policy_stats[p]["triggers"] += 1
                    risk = record.get("risk", "")
                    if risk == "BLOCK":
                        policy_stats[p]["blocks"] += 1
                    elif risk == "REVIEW_REQUIRED":
                        policy_stats[p]["reviews"] += 1

                if record.get("type") == "override":
                    for p in record.get("matched_policies", []):
                        if p in policy_stats:
                            policy_stats[p]["overrides"] += 1

        return [
            {"policy": name, **stats}
            for name, stats in sorted(policy_stats.items(), key=lambda x: x[1]["triggers"], reverse=True)
        ]
