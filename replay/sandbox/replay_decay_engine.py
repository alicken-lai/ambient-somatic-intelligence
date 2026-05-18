"""Replay Decay Engine — wraps the production DecayEngine for replay context.

Applies decay rules to replay memories without affecting any production
confidence scores.  All decay events are tracked in a dedicated audit
trail for post-replay analysis.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.decay_engine import DecayEngine, DecayReport
from memory.ontology.decay_rules import DECAY_RULES, DecayRule
from memory.ontology.layer_definition import MemoryLayer

from .replay_config import ReplayConfig
from .replay_memory_store import ReplayMemoryStore


@dataclass
class ReplayDecayEvent:
    """A single decay application during replay."""

    report: DecayReport
    applied_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    written_to_store: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "report": self.report.to_dict(),
            "applied_at": self.applied_at.isoformat(),
            "written_to_store": self.written_to_store,
        }


class ReplayDecayEngine:
    """Wraps :class:`DecayEngine` to operate on replay data only.

    Key differences from production:
      - Operates on shallow copies of entries so originals are not mutated
        when entries are passed from external sources.
      - Writes confidence changes back to the :class:`ReplayMemoryStore`.
      - Tracks every decay event for post-replay auditing.
    """

    def __init__(
        self,
        store: ReplayMemoryStore,
        config: ReplayConfig,
        rules: list[DecayRule] | None = None,
        confidence_model: ConfidenceModel | None = None,
    ) -> None:
        self._store = store
        self._config = config
        self._confidence_model = confidence_model or ConfidenceModel()
        self._rules = rules or list(DECAY_RULES)
        self._engine = DecayEngine(self._rules, self._confidence_model)
        self._events: list[ReplayDecayEvent] = []
        self._audit: list[dict[str, Any]] = []

    # ── Core decay operations ─────────────────────────────────────────

    def apply_time_decay(
        self,
        entries: list[Any],
        current_time: datetime,
    ) -> list[DecayReport]:
        """Apply time-based decay to copies of entries, then sync to store."""
        clones = self._clone_entries(entries)
        reports = self._engine.apply_time_decay(clones, current_time)
        self._sync_to_store(clones, reports)
        return reports

    def apply_inactivity_decay(
        self,
        entries: list[Any],
        current_time: datetime,
    ) -> list[DecayReport]:
        """Apply inactivity decay to copies of entries, then sync to store."""
        clones = self._clone_entries(entries)
        reports = self._engine.apply_inactivity_decay(clones, current_time)
        self._sync_to_store(clones, reports)
        return reports

    def sweep(
        self,
        entries: list[Any],
        current_time: datetime,
    ) -> list[DecayReport]:
        """Full decay sweep (time + inactivity), then sync to store."""
        clones = self._clone_entries(entries)
        reports = self._engine.sweep(clones, current_time)
        self._sync_to_store(clones, reports)
        return reports

    def apply_contradiction(
        self,
        entry: Any,
        evidence: str,
    ) -> DecayReport:
        """Apply contradiction penalty to a copy, then sync to store."""
        clone = copy.copy(entry)
        report = self._engine.apply_contradiction(clone, evidence)
        self._sync_single(clone, report)
        return report

    def apply_failed_reuse(
        self,
        entry: Any,
        context: str,
    ) -> DecayReport:
        """Apply failure penalty to a copy, then sync to store."""
        clone = copy.copy(entry)
        report = self._engine.apply_failed_reuse(clone, context)
        self._sync_single(clone, report)
        return report

    def get_at_risk_entries(
        self,
        entries: list[Any],
        current_time: datetime,
    ) -> list[DecayReport]:
        """Identify entries approaching removal threshold (read-only)."""
        return self._engine.get_at_risk_entries(entries, current_time)

    # ── Batch processing ─────────────────────────────────────────────

    def process_all_layers(
        self,
        current_time: datetime | None = None,
    ) -> list[DecayReport]:
        """Run a full decay sweep across every layer in the replay store.

        Builds temporary entry proxies from the store's ReplayEntry
        objects so that the production DecayEngine can process them.
        """
        now = current_time or datetime.now(timezone.utc)
        all_reports: list[DecayReport] = []

        for layer in MemoryLayer:
            replay_entries = self._store.get_all(layer)
            if not replay_entries:
                continue

            proxies = [_EntryProxy(re) for re in replay_entries]
            reports = self.sweep(proxies, now)
            all_reports.extend(reports)

        self._audit.append({
            "action": "process_all_layers",
            "current_time": now.isoformat(),
            "total_reports": len(all_reports),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return all_reports

    # ── Query & Export ────────────────────────────────────────────────

    @property
    def events(self) -> list[ReplayDecayEvent]:
        return list(self._events)

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit)

    @property
    def total_decayed(self) -> int:
        return len(self._events)

    @property
    def entries_removed(self) -> int:
        return sum(1 for e in self._events if e.report.recommended_action == "remove")

    def generate_report(self) -> str:
        """Delegate to the production engine's report generator."""
        reports = [e.report for e in self._events]
        return self._engine.generate_report(reports)

    def export_results(self) -> dict[str, Any]:
        return {
            "total_decayed": self.total_decayed,
            "entries_removed": self.entries_removed,
            "events": [e.to_dict() for e in self._events],
            "audit_log": self._audit,
        }

    # ── Internal helpers ─────────────────────────────────────────────

    def _clone_entries(self, entries: list[Any]) -> list[Any]:
        return [copy.copy(e) for e in entries]

    def _sync_to_store(
        self,
        clones: list[Any],
        reports: list[DecayReport],
    ) -> None:
        """Write back confidence changes from decay reports to the store."""
        report_map = {r.entry_id: r for r in reports}
        for clone in clones:
            report = report_map.get(clone.entry_id)
            if report is None:
                continue
            written = self._store.update_confidence(
                entry_id=clone.entry_id,
                layer=clone.layer,
                new_confidence=report.new_confidence,
                reason=f"decay:{report.decay_reason}",
            )
            event = ReplayDecayEvent(
                report=report,
                written_to_store=written,
            )
            self._events.append(event)

    def _sync_single(self, clone: Any, report: DecayReport) -> None:
        written = self._store.update_confidence(
            entry_id=clone.entry_id,
            layer=clone.layer,
            new_confidence=report.new_confidence,
            reason=f"decay:{report.decay_reason}",
        )
        self._events.append(ReplayDecayEvent(
            report=report,
            written_to_store=written,
        ))


class _EntryProxy:
    """Proxy that adapts a ReplayEntry to the interface expected by DecayEngine."""

    def __init__(self, replay_entry: Any) -> None:
        self.entry_id: str = replay_entry.entry_id
        self.layer: MemoryLayer = replay_entry.layer
        self.confidence: float = replay_entry.confidence
        self.timestamp: datetime = replay_entry.timestamp
        payload = getattr(replay_entry, "payload", {})
        self.last_accessed = self._extract_dt(payload, "last_accessed")
        self.last_validated = self._extract_dt(payload, "last_validated")
        self.last_executed = self._extract_dt(payload, "last_executed")
        self.last_applied = self._extract_dt(payload, "last_applied")

    @staticmethod
    def _extract_dt(payload: dict, key: str) -> datetime | None:
        val = payload.get(key)
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return None
        return None
