"""
Escalation Router — Formal escalation with governance integration.

Evaluates each signal and decides one of five actions:

  ATTEND   — handle within current attention budget
  DEFER    — queue for later processing
  ESCALATE — requires governance / operator attention
  THROTTLE — too many signals, apply backpressure
  IGNORE   — below threshold, log and discard

All decisions are logged with full provenance for audit.
Integrates with ``governance.policy_engine.RiskLevel`` so that
BLOCK-level governance signals always escalate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from attention.attention_state import AttentionSignal, AttentionSnapshot
from attention.salience_engine import SalienceScore
from governance.policy_engine import RiskLevel

logger = logging.getLogger(__name__)


class EscalationAction(str, Enum):
    """Possible escalation outcomes."""
    ATTEND = "attend"
    DEFER = "defer"
    ESCALATE = "escalate"
    THROTTLE = "throttle"
    IGNORE = "ignore"


@dataclass
class EscalationDecision:
    """Result of an escalation evaluation."""
    signal_id: str
    action: EscalationAction
    target: str
    reason: str
    governance_required: bool
    salience_total: float
    decided_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "action": self.action.value,
            "target": self.target,
            "reason": self.reason,
            "governance_required": self.governance_required,
            "salience_total": round(self.salience_total, 4),
            "decided_at": self.decided_at.isoformat(),
        }


class EscalationRouter:
    """
    Routes attention signals to the correct handler / escalation path.

    Usage::

        router = EscalationRouter()
        decision = router.evaluate(signal, salience, state)
        if decision.action == EscalationAction.ESCALATE:
            notify_operator(decision)
    """

    def __init__(
        self,
        attend_threshold: float = 0.30,
        escalate_threshold: float = 0.75,
        throttle_active_limit: int = 15,
        ignore_threshold: float = 0.10,
    ) -> None:
        self._attend_threshold = attend_threshold
        self._escalate_threshold = escalate_threshold
        self._throttle_limit = throttle_active_limit
        self._ignore_threshold = ignore_threshold
        self._decision_log: list[EscalationDecision] = []
        self._max_log = 500

    # ------------------------------------------------------------------
    # Core evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        signal: AttentionSignal,
        salience: SalienceScore,
        state: AttentionSnapshot,
    ) -> EscalationDecision:
        """
        Decide the escalation action for *signal* in the context of the
        current attention *state*.
        """
        gov_risk = self._governance_risk(signal)

        if gov_risk == RiskLevel.BLOCK:
            decision = self._decide_escalate(
                signal, salience,
                reason="Governance BLOCK-level risk — immediate escalation required",
            )
        elif salience.total < self._ignore_threshold:
            decision = self._decide_ignore(signal, salience)
        elif self._is_throttled(state):
            decision = self._decide_throttle(signal, salience, state)
        elif salience.total >= self._escalate_threshold or gov_risk == RiskLevel.REVIEW_REQUIRED:
            decision = self._decide_escalate(signal, salience)
        elif salience.total >= self._attend_threshold:
            decision = self._decide_attend(signal, salience)
        else:
            decision = self._decide_defer(signal, salience)

        self._log_decision(decision)
        return decision

    # ------------------------------------------------------------------
    # Decision builders
    # ------------------------------------------------------------------

    def _decide_attend(
        self,
        signal: AttentionSignal,
        salience: SalienceScore,
    ) -> EscalationDecision:
        return EscalationDecision(
            signal_id=signal.signal_id,
            action=EscalationAction.ATTEND,
            target="attention_layer",
            reason=f"Within budget (salience={salience.total:.3f})",
            governance_required=False,
            salience_total=salience.total,
        )

    def _decide_defer(
        self,
        signal: AttentionSignal,
        salience: SalienceScore,
    ) -> EscalationDecision:
        return EscalationDecision(
            signal_id=signal.signal_id,
            action=EscalationAction.DEFER,
            target="deferred_queue",
            reason=f"Below attend threshold (salience={salience.total:.3f})",
            governance_required=False,
            salience_total=salience.total,
        )

    def _decide_escalate(
        self,
        signal: AttentionSignal,
        salience: SalienceScore,
        reason: str | None = None,
    ) -> EscalationDecision:
        return EscalationDecision(
            signal_id=signal.signal_id,
            action=EscalationAction.ESCALATE,
            target="governance_operator",
            reason=reason or f"High salience requires escalation (salience={salience.total:.3f})",
            governance_required=True,
            salience_total=salience.total,
        )

    def _decide_throttle(
        self,
        signal: AttentionSignal,
        salience: SalienceScore,
        state: AttentionSnapshot,
    ) -> EscalationDecision:
        return EscalationDecision(
            signal_id=signal.signal_id,
            action=EscalationAction.THROTTLE,
            target="backpressure",
            reason=(
                f"Active signal count ({len(state.active_signals)}) "
                f"exceeds throttle limit ({self._throttle_limit})"
            ),
            governance_required=False,
            salience_total=salience.total,
        )

    def _decide_ignore(
        self,
        signal: AttentionSignal,
        salience: SalienceScore,
    ) -> EscalationDecision:
        return EscalationDecision(
            signal_id=signal.signal_id,
            action=EscalationAction.IGNORE,
            target="log_only",
            reason=f"Below ignore threshold (salience={salience.total:.3f})",
            governance_required=False,
            salience_total=salience.total,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _governance_risk(signal: AttentionSignal) -> RiskLevel:
        """Extract governance risk level from signal metadata."""
        raw = signal.metadata.get("governance_risk_level")
        if raw is None:
            return RiskLevel.ALLOW
        if isinstance(raw, int):
            return RiskLevel(raw)
        return RiskLevel.from_str(str(raw))

    def _is_throttled(self, state: AttentionSnapshot) -> bool:
        """Check whether the attention layer is overloaded."""
        return len(state.active_signals) >= self._throttle_limit

    def _log_decision(self, decision: EscalationDecision) -> None:
        """Persist the decision for audit / provenance."""
        self._decision_log.append(decision)
        if len(self._decision_log) > self._max_log:
            self._decision_log = self._decision_log[-self._max_log:]

        logger.info(
            "Escalation decision: signal=%s action=%s target=%s reason='%s' governance=%s",
            decision.signal_id[:8],
            decision.action.value,
            decision.target,
            decision.reason,
            decision.governance_required,
        )

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def recent_decisions(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent escalation decisions."""
        return [d.to_dict() for d in self._decision_log[-limit:]]

    def decision_stats(self) -> dict[str, int]:
        """Count decisions by action type."""
        stats: dict[str, int] = {a.value: 0 for a in EscalationAction}
        for d in self._decision_log:
            stats[d.action.value] += 1
        return stats
