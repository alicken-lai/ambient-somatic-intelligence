"""In-process idempotency and first-class trajectory ledger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from hermes.orchestration.envelopes import ProposedActionEnvelope, ResultEvidenceEnvelope, TrajectoryEvent


ReplayState = Literal["new", "pending", "completed", "conflict"]


@dataclass(frozen=True)
class ReplayReservation:
    state: ReplayState
    prior_result: ResultEvidenceEnvelope | None = None


@dataclass
class _Record:
    action_digest: str
    result: ResultEvidenceEnvelope | None = None


class ReplayLedger:
    """Fail-closed in-process guard; durable sinks consume its emitted envelopes."""

    def __init__(self) -> None:
        self._records: dict[str, _Record] = {}
        self.events: list[TrajectoryEvent] = []

    def reserve(self, proposal: ProposedActionEnvelope) -> ReplayReservation:
        digest = proposal.action_digest()
        record = self._records.get(proposal.idempotency_key)
        if record is None:
            self._records[proposal.idempotency_key] = _Record(action_digest=digest)
            return ReplayReservation("new")
        if record.action_digest != digest:
            return ReplayReservation("conflict", record.result)
        if record.result is None:
            return ReplayReservation("pending")
        return ReplayReservation("completed", record.result)

    def append(self, event: TrajectoryEvent) -> None:
        self.events.append(event)

    def complete(self, idempotency_key: str, evidence: ResultEvidenceEnvelope) -> None:
        record = self._records.get(idempotency_key)
        if record is None:
            raise RuntimeError("idempotency key was not reserved")
        if record.result is not None:
            raise RuntimeError("result evidence is append-only and already complete")
        record.result = evidence

    def record_steering(self, event: TrajectoryEvent) -> None:
        if event.event_type != "steering_update":
            raise ValueError("record_steering requires a steering_update event")
        self.append(event)

