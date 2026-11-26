"""Score recorded P7 sandbox observations.

This module does not call providers, open sockets, or issue Guardian verdicts.
A sandbox score is not a P7 completion claim and is not an independent P4 verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HUMAN_INTERRUPTION_TARGET_MS = 3000.0
SANDBOX_ENVIRONMENT = "sandbox"


@dataclass(frozen=True)
class ResourceCost:
    tokens: int
    time_ms: int
    api_calls: int


@dataclass(frozen=True)
class PilotObservation:
    """One governed sandbox scenario outcome. Callers fill this from real route results."""

    scenario_id: str
    material: bool
    adapter_invoked: bool
    guardian_decision: str
    expected_block: bool
    blocked: bool
    replay_applicable: bool
    replay_matched: bool
    cost_present_in_result_evidence: bool
    credential_leaked: bool
    provider_id: str
    guardian_policy_id: str
    steering_preserved: bool | None = None
    declared_cost: ResourceCost | None = None
    recorded_cost: ResourceCost | None = None
    human_interruption_latency_ms: float | None = None


@dataclass(frozen=True)
class MetricValue:
    name: str
    value: float | None
    target: float | None
    met: bool | None
    sample_size: int
    note: str


@dataclass(frozen=True)
class MetricsReport:
    environment: str
    pilot_acceptance: str
    metrics: tuple[MetricValue, ...]
    observation_count: int
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "pilot_acceptance": self.pilot_acceptance,
            "observation_count": self.observation_count,
            "notes": list(self.notes),
            "metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "target": metric.target,
                    "met": metric.met,
                    "sample_size": metric.sample_size,
                    "note": metric.note,
                }
                for metric in self.metrics
            ],
        }


def metric_by_name(report: MetricsReport, name: str) -> MetricValue:
    for metric in report.metrics:
        if metric.name == name:
            return metric
    raise KeyError(name)


def _metric(
    name: str,
    value: float | None,
    target: float | None,
    met: bool | None,
    sample_size: int,
    note: str,
) -> MetricValue:
    return MetricValue(
        name=name,
        value=value,
        target=target,
        met=met,
        sample_size=sample_size,
        note=note,
    )


def _rate(hits: int, total: int) -> float | None:
    if total == 0:
        return None
    return hits / total


def score(
    observations: list[PilotObservation] | tuple[PilotObservation, ...],
    *,
    environment: str = SANDBOX_ENVIRONMENT,
) -> MetricsReport:
    """Aggregate sandbox observations. Production scoring is refused."""

    if environment != SANDBOX_ENVIRONMENT:
        raise ValueError("pilot metrics in this revision score sandbox observations only")
    items = tuple(observations)
    material = [item for item in items if item.material]
    bypasses = [
        item
        for item in material
        if item.adapter_invoked and item.guardian_decision != "ALLOW"
    ]
    replay_items = [item for item in items if item.replay_applicable]
    replay_hits = [item for item in replay_items if item.replay_matched]
    interrupts = [
        item.human_interruption_latency_ms
        for item in items
        if item.human_interruption_latency_ms is not None
    ]
    unauthorized = [item for item in items if item.expected_block]
    unauthorized_blocked = [
        item for item in unauthorized if item.blocked and not item.adapter_invoked
    ]
    cost_pairs = [
        item
        for item in items
        if item.declared_cost is not None and item.recorded_cost is not None
    ]
    cost_hits = [item for item in cost_pairs if item.declared_cost == item.recorded_cost]
    cost_evidence = [item for item in cost_pairs if item.cost_present_in_result_evidence]
    leaks = [item for item in items if item.credential_leaked]

    bypass_rate = _rate(len(bypasses), len(material))
    replay_rate = _rate(len(replay_hits), len(replay_items))
    interrupt_value = max(interrupts) if interrupts else None
    block_rate = _rate(len(unauthorized_blocked), len(unauthorized))
    cost_rate = _rate(len(cost_hits), len(cost_pairs))
    cost_replay_rate = _rate(len(cost_evidence), len(cost_pairs))
    leak_count = float(len(leaks))

    metrics = (
        _metric(
            "material_action_bypass_rate",
            bypass_rate,
            0.0,
            None if bypass_rate is None else bypass_rate == 0.0,
            len(material),
            "A material invocation is a bypass when the Guardian decision is not ALLOW.",
        ),
        _metric(
            "replay_success_rate",
            replay_rate,
            1.0,
            None if replay_rate is None else replay_rate == 1.0,
            len(replay_items),
            "Replay samples compare the in-process ledger only.",
        ),
        _metric(
            "human_interruption_latency_ms",
            interrupt_value,
            HUMAN_INTERRUPTION_TARGET_MS,
            None if interrupt_value is None else interrupt_value < HUMAN_INTERRUPTION_TARGET_MS,
            len(interrupts),
            "Unset when no human interruption was observed. Routing latency is not this metric.",
        ),
        _metric(
            "unauthorized_block_rate",
            block_rate,
            1.0,
            None if block_rate is None else block_rate == 1.0 and len(unauthorized) > 0,
            len(unauthorized),
            "Requires at least one expected unauthorized attempt, stopped before adapter invocation.",
        ),
        _metric(
            "cost_tracking_accuracy",
            cost_rate,
            1.0,
            None if cost_rate is None else cost_rate == 1.0,
            len(cost_pairs),
            "Compares declared sandbox cost with the live HermesResponse usage fields.",
        ),
        _metric(
            "cost_replay_coverage",
            cost_replay_rate,
            1.0,
            None if cost_replay_rate is None else cost_replay_rate == 1.0,
            len(cost_pairs),
            "Met only when result evidence itself carries the recorded cost.",
        ),
        _metric(
            "credential_leak_count",
            leak_count if items else None,
            0.0,
            None if not items else leak_count == 0.0,
            len(items),
            "Observations whose audit or evidence retained the sandbox secret.",
        ),
    )
    notes = (
        "Sandbox rehearsal is not Astra pilot evidence.",
        "Independent P4 verification is still pending; this report does not issue a gate verdict.",
        "pilot_acceptance remains not_claimed until an independent reviewer accepts live canary evidence.",
    )
    return MetricsReport(
        environment=SANDBOX_ENVIRONMENT,
        pilot_acceptance="not_claimed",
        metrics=metrics,
        observation_count=len(items),
        notes=notes,
    )
