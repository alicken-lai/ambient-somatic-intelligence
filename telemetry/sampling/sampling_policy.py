"""
Sampling Policy — Declarative cadence and failure-handling policies.

Every telemetry source must declare a SamplingPolicy that specifies its
desired cadence, jitter tolerance, retry strategy, and failure escalation
path.  The hard ceiling is 300 seconds (5 minutes) unless a governance
exception has been granted.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_CADENCE_SECONDS = 300


@dataclass(frozen=True)
class SamplingPolicy:
    """Immutable sampling policy for a telemetry source."""

    source_name: str
    desired_cadence_seconds: int
    allowed_jitter_seconds: int
    retry_count: int
    retry_delay_seconds: int
    failure_escalation: str  # "log" | "alert" | "guardian"
    priority: str            # "critical" | "standard" | "low"
    governance_exception: bool = False
    governance_exception_id: str = ""

    def __post_init__(self) -> None:
        if self.desired_cadence_seconds > MAX_CADENCE_SECONDS and not self.governance_exception:
            raise ValueError(
                f"Cadence {self.desired_cadence_seconds}s exceeds max {MAX_CADENCE_SECONDS}s "
                f"and no governance exception is granted for source '{self.source_name}'"
            )
        if self.desired_cadence_seconds <= 0:
            raise ValueError(
                f"Cadence must be positive, got {self.desired_cadence_seconds}s "
                f"for source '{self.source_name}'"
            )
        if self.failure_escalation not in ("log", "alert", "guardian"):
            raise ValueError(
                f"Invalid failure_escalation '{self.failure_escalation}'; "
                f"must be one of: log, alert, guardian"
            )
        if self.priority not in ("critical", "standard", "low"):
            raise ValueError(
                f"Invalid priority '{self.priority}'; "
                f"must be one of: critical, standard, low"
            )

    @property
    def effective_cadence_seconds(self) -> int:
        return self.desired_cadence_seconds

    @property
    def max_acceptable_interval_seconds(self) -> int:
        return self.desired_cadence_seconds + self.allowed_jitter_seconds

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "desired_cadence_seconds": self.desired_cadence_seconds,
            "allowed_jitter_seconds": self.allowed_jitter_seconds,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "failure_escalation": self.failure_escalation,
            "priority": self.priority,
            "governance_exception": self.governance_exception,
            "governance_exception_id": self.governance_exception_id,
        }


# ── Predefined policies ──────────────────────────────────────────────────

CRITICAL_5MIN = SamplingPolicy(
    source_name="__template_critical_5min__",
    desired_cadence_seconds=300,
    allowed_jitter_seconds=0,
    retry_count=3,
    retry_delay_seconds=10,
    failure_escalation="guardian",
    priority="critical",
)

STANDARD_5MIN = SamplingPolicy(
    source_name="__template_standard_5min__",
    desired_cadence_seconds=300,
    allowed_jitter_seconds=30,
    retry_count=2,
    retry_delay_seconds=15,
    failure_escalation="alert",
    priority="standard",
)

HIGH_FREQ_1MIN = SamplingPolicy(
    source_name="__template_high_freq_1min__",
    desired_cadence_seconds=60,
    allowed_jitter_seconds=10,
    retry_count=3,
    retry_delay_seconds=5,
    failure_escalation="guardian",
    priority="critical",
)

BACKGROUND_5MIN = SamplingPolicy(
    source_name="__template_background_5min__",
    desired_cadence_seconds=300,
    allowed_jitter_seconds=60,
    retry_count=1,
    retry_delay_seconds=30,
    failure_escalation="log",
    priority="low",
)


def make_policy(
    source_name: str,
    template: SamplingPolicy,
    **overrides: object,
) -> SamplingPolicy:
    """Create a named policy from a template, with optional overrides."""
    base = template.to_dict()
    base["source_name"] = source_name
    base.update(overrides)
    return SamplingPolicy(**base)
