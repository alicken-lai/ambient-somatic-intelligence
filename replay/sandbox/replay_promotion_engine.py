"""Replay Promotion Engine — wraps the production PromotionEngine.

Redirects all writes to the :class:`ReplayMemoryStore` so that no
production data is ever mutated.  Supports dry-run mode and maintains
a full audit trail of every promotion decision.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from memory.ontology.confidence_model import ConfidenceModel
from memory.ontology.layer_definition import MemoryLayer
from memory.ontology.promotion_engine import (
    PromotionCandidate,
    PromotionEngine,
    PromotionResult,
)
from memory.ontology.promotion_rules import (
    PROMOTION_RULES,
    PromotionRule,
    check_promotion_eligibility,
)

from .replay_config import ReplayConfig
from .replay_memory_store import ReplayEntry, ReplayMemoryStore


@dataclass
class ReplayPromotionRecord:
    """Immutable record of a single promotion decision during replay."""

    candidate: PromotionCandidate
    result: PromotionResult
    replayed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "result": self.result.to_dict(),
            "replayed_at": self.replayed_at.isoformat(),
            "dry_run": self.dry_run,
        }


class ReplayPromotionEngine:
    """Wraps :class:`PromotionEngine` for sandboxed replay.

    Key differences from the production engine:
      - Promoted entries are written to the replay memory store, not disk.
      - Dry-run mode skips the actual store write but still records decisions.
      - A dedicated audit trail captures every scan/propose/approve cycle.
      - Deterministic candidate IDs when ``config.deterministic_ids`` is set.
    """

    def __init__(
        self,
        store: ReplayMemoryStore,
        config: ReplayConfig,
        rules: list[PromotionRule] | None = None,
        confidence_model: ConfidenceModel | None = None,
    ) -> None:
        self._store = store
        self._config = config
        self._confidence_model = confidence_model or ConfidenceModel()
        self._rules = rules or list(PROMOTION_RULES)
        self._engine = PromotionEngine(self._rules, self._confidence_model)
        self._records: list[ReplayPromotionRecord] = []
        self._audit: list[dict[str, Any]] = []
        self._id_counter: int = 0

    # ── Scanning ──────────────────────────────────────────────────────

    def scan_candidates(
        self,
        entries: list[Any],
        layer: MemoryLayer,
    ) -> list[PromotionCandidate]:
        """Delegate to the production engine's scan logic."""
        candidates = self._engine.scan_candidates(entries, layer)
        self._audit.append({
            "action": "scan_candidates",
            "layer": layer.value,
            "entries_scanned": len(entries),
            "candidates_found": len(candidates),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return candidates

    # ── Proposal + Approval (single step for replay) ─────────────────

    def propose_and_decide(
        self,
        candidate: PromotionCandidate,
        governance_decision_id: str | None = None,
        verifier_id: str | None = None,
    ) -> ReplayPromotionRecord:
        """Propose a candidate and immediately decide in replay context.

        In replay mode with ``auto_approve_for_replay`` the governance
        decision is synthesised automatically.  In dry-run mode the
        decision is recorded but nothing is written to the store.
        """
        self._engine.propose_promotion(candidate)

        gov_id = governance_decision_id
        if gov_id is None and self._config.auto_approve_for_replay:
            gov_id = f"replay-gov-{self._next_id()}"

        if gov_id is None and self._config.enforce_governance:
            result = self._engine.reject_promotion(
                candidate.candidate_id,
                "No governance decision provided and auto-approve is disabled",
            )
        else:
            effective_gov_id = gov_id or f"replay-gov-{self._next_id()}"
            effective_verifier = verifier_id
            if (
                candidate.target_layer == MemoryLayer.L4_STRATEGIC
                and not effective_verifier
                and self._config.auto_approve_for_replay
            ):
                effective_verifier = f"replay-verifier-{self._next_id()}"

            result = self._engine.approve_promotion(
                candidate.candidate_id,
                governance_decision_id=effective_gov_id,
                verifier_id=effective_verifier,
            )

        record = ReplayPromotionRecord(
            candidate=candidate,
            result=result,
            dry_run=self._config.dry_run,
        )
        self._records.append(record)

        if result.approved and not self._config.dry_run:
            self._store.promote(
                entry_id=candidate.entry_id,
                source_layer=candidate.source_layer,
                target_layer=candidate.target_layer,
                new_entry_id=result.new_entry_id or f"replay-{self._next_id()}",
                confidence=candidate.confidence,
            )

        self._audit.append({
            "action": "propose_and_decide",
            "candidate_id": candidate.candidate_id,
            "entry_id": candidate.entry_id,
            "source_layer": candidate.source_layer.value,
            "target_layer": candidate.target_layer.value,
            "approved": result.approved,
            "reason": result.reason,
            "dry_run": self._config.dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return record

    # ── Batch processing ─────────────────────────────────────────────

    def process_layer(
        self,
        entries: list[Any],
        layer: MemoryLayer,
    ) -> list[ReplayPromotionRecord]:
        """Scan, propose, and decide all candidates from a layer."""
        candidates = self.scan_candidates(entries, layer)
        records: list[ReplayPromotionRecord] = []
        for candidate in candidates:
            if candidate.eligible:
                record = self.propose_and_decide(candidate)
                records.append(record)
        return records

    # ── Query ─────────────────────────────────────────────────────────

    @property
    def records(self) -> list[ReplayPromotionRecord]:
        return list(self._records)

    @property
    def approved_count(self) -> int:
        return sum(1 for r in self._records if r.result.approved)

    @property
    def rejected_count(self) -> int:
        return sum(1 for r in self._records if not r.result.approved)

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit)

    def export_results(self) -> dict[str, Any]:
        return {
            "total_records": len(self._records),
            "approved": self.approved_count,
            "rejected": self.rejected_count,
            "dry_run": self._config.dry_run,
            "records": [r.to_dict() for r in self._records],
            "audit_log": self._audit,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    def _next_id(self) -> str:
        if self._config.deterministic_ids:
            self._id_counter += 1
            return f"{self._id_counter:06d}"
        return uuid.uuid4().hex[:12]
