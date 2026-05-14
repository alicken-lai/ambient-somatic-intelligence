"""
Governance Load Analytics — Analytics on governance system load and effectiveness.

Monitors the governance layer's operational health:
  - Throughput: How many gate checks per minute
  - Latency: How long each check takes
  - Outcomes: Approval, denial, and review rates
  - Bottleneck detection: Is governance slowing the system?
  - Effectiveness: Are blocks preventing real problems?

Enables governance tuning by surfacing:
  - False positive rates (unnecessary blocks)
  - True positive rates (blocks that prevented real issues)
  - Bottleneck score (governance as a system constraint)
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GateCheckEvent:
    """A single governance gate check."""
    action: str
    agent_id: str
    result: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "action": self.action,
            "agent_id": self.agent_id,
            "result": self.result,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GovernanceLoadReport:
    """Governance load and effectiveness report."""
    checks_per_minute: float = 0.0
    avg_latency_ms: float = 0.0
    approval_rate: float = 0.0
    denial_rate: float = 0.0
    review_rate: float = 0.0
    bottleneck_score: float = 0.0
    effectiveness_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "checks_per_minute": round(self.checks_per_minute, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "approval_rate": round(self.approval_rate, 4),
            "denial_rate": round(self.denial_rate, 4),
            "review_rate": round(self.review_rate, 4),
            "bottleneck_score": round(self.bottleneck_score, 4),
            "effectiveness_score": round(self.effectiveness_score, 4),
        }


@dataclass
class GovernanceEffectivenessReport:
    """Detailed governance effectiveness analysis."""
    true_positive_rate: float = 0.0
    false_positive_rate: float = 0.0
    bottleneck_detected: bool = False
    bottleneck_details: str = ""
    total_checks: int = 0
    total_blocks: int = 0
    confirmed_threats: int = 0
    false_blocks: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "true_positive_rate": round(self.true_positive_rate, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "bottleneck_detected": self.bottleneck_detected,
            "bottleneck_details": self.bottleneck_details,
            "total_checks": self.total_checks,
            "total_blocks": self.total_blocks,
            "confirmed_threats": self.confirmed_threats,
            "false_blocks": self.false_blocks,
        }


class GovernanceLoadAnalytics:
    """
    Analytics on governance system load and effectiveness.

    Tracks gate check throughput, latency, outcome distributions,
    and effectiveness metrics to enable governance optimization.

    Usage:
        analytics = GovernanceLoadAnalytics()

        analytics.track_gate_check(
            action="execute_shell",
            agent_id="backend-agent",
            result="ALLOW",
            duration=0.012,
        )

        load = analytics.get_governance_load()
        effectiveness = analytics.get_governance_effectiveness()
    """

    def __init__(self, max_events: int = 5000, bottleneck_threshold_ms: float = 100.0):
        self._events: list[GateCheckEvent] = []
        self._event_timestamps: deque[float] = deque(maxlen=max_events)
        self._max_events = max_events
        self._bottleneck_threshold_ms = bottleneck_threshold_ms
        self._confirmed_threats: int = 0
        self._false_blocks: int = 0

    def track_gate_check(
        self,
        action: str,
        agent_id: str,
        result: str,
        duration: float,
        metadata: dict[str, Any] | None = None,
    ) -> GateCheckEvent:
        """
        Track a governance gate check.

        Args:
            action: The action being checked
            agent_id: Agent requesting the action
            result: Check outcome (ALLOW, DENY, REVIEW)
            duration: Check duration in seconds
            metadata: Additional context
        """
        event = GateCheckEvent(
            action=action,
            agent_id=agent_id,
            result=result.upper(),
            duration_ms=duration * 1000,
            metadata=metadata or {},
        )

        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        self._event_timestamps.append(event.timestamp)

        logger.debug(
            "Gate check: action=%s agent=%s result=%s %.1fms",
            action, agent_id, result, event.duration_ms
        )
        return event

    def record_threat_confirmation(self, was_real_threat: bool) -> None:
        """
        Record whether a governance block was a true or false positive.

        Call this after a blocked action is reviewed to track effectiveness.
        """
        if was_real_threat:
            self._confirmed_threats += 1
        else:
            self._false_blocks += 1

    def get_governance_load(self) -> GovernanceLoadReport:
        """
        Get current governance throughput and load metrics.

        Returns:
            GovernanceLoadReport with throughput, latency, and outcome rates
        """
        if not self._events:
            return GovernanceLoadReport()

        now = time.time()
        one_minute_ago = now - 60.0

        recent = [e for e in self._events if e.timestamp >= one_minute_ago]
        checks_per_minute = len(recent)

        all_latencies = [e.duration_ms for e in self._events]
        avg_latency = sum(all_latencies) / len(all_latencies)

        total = len(self._events)
        approvals = sum(1 for e in self._events if e.result == "ALLOW")
        denials = sum(1 for e in self._events if e.result == "DENY")
        reviews = sum(1 for e in self._events if e.result == "REVIEW")

        bottleneck_score = self._compute_bottleneck_score(avg_latency, checks_per_minute)

        effectiveness_score = self._compute_effectiveness_score()

        return GovernanceLoadReport(
            checks_per_minute=float(checks_per_minute),
            avg_latency_ms=avg_latency,
            approval_rate=approvals / total,
            denial_rate=denials / total,
            review_rate=reviews / total,
            bottleneck_score=bottleneck_score,
            effectiveness_score=effectiveness_score,
        )

    def get_governance_effectiveness(self) -> GovernanceEffectivenessReport:
        """
        Analyze governance effectiveness.

        Returns:
            GovernanceEffectivenessReport with true/false positive rates and bottleneck detection
        """
        total_blocks = sum(1 for e in self._events if e.result in ("DENY", "REVIEW"))

        true_positive_rate = 0.0
        false_positive_rate = 0.0

        total_confirmed = self._confirmed_threats + self._false_blocks
        if total_confirmed > 0:
            true_positive_rate = self._confirmed_threats / total_confirmed
            false_positive_rate = self._false_blocks / total_confirmed

        avg_latency = 0.0
        if self._events:
            avg_latency = sum(e.duration_ms for e in self._events) / len(self._events)

        bottleneck_detected = avg_latency > self._bottleneck_threshold_ms
        bottleneck_details = ""
        if bottleneck_detected:
            bottleneck_details = (
                f"Average gate latency ({avg_latency:.1f}ms) exceeds "
                f"threshold ({self._bottleneck_threshold_ms:.1f}ms). "
                f"Consider caching frequent checks or relaxing low-risk policies."
            )

        return GovernanceEffectivenessReport(
            true_positive_rate=true_positive_rate,
            false_positive_rate=false_positive_rate,
            bottleneck_detected=bottleneck_detected,
            bottleneck_details=bottleneck_details,
            total_checks=len(self._events),
            total_blocks=total_blocks,
            confirmed_threats=self._confirmed_threats,
            false_blocks=self._false_blocks,
        )

    def _compute_bottleneck_score(self, avg_latency: float, checks_per_minute: float) -> float:
        """
        Compute bottleneck score (0.0 to 1.0).

        Higher score indicates governance is becoming a system constraint.
        Factors: latency relative to threshold, throughput pressure.
        """
        latency_factor = min(1.0, avg_latency / (self._bottleneck_threshold_ms * 2))
        throughput_factor = min(1.0, checks_per_minute / 100.0)
        return min(1.0, (latency_factor * 0.7) + (throughput_factor * 0.3))

    def _compute_effectiveness_score(self) -> float:
        """
        Compute overall effectiveness score (0.0 to 1.0).

        Based on true positive rate and denial coverage.
        """
        total_confirmed = self._confirmed_threats + self._false_blocks
        if total_confirmed == 0:
            return 1.0

        true_positive_rate = self._confirmed_threats / total_confirmed
        return true_positive_rate
