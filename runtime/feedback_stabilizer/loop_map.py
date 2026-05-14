from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class FeedbackLoop:
    id: str
    name: str
    status: str
    severity: str
    path: list[str]
    description: str
    existing_safeguards: list[str]
    missing_safeguards: list[str]
    amplification_factor: float
    damping_recommendation: str


@dataclass
class AmplificationPath:
    id: str
    name: str
    source_loop: str
    target_loop: str
    trigger_condition: str
    max_amplification: float
    cooldown_protection: str


@dataclass
class LoopMapReport:
    total_loops: int
    active: int
    guarded: int
    latent: int
    max_amplification: float
    cross_amplification_paths: int
    overall_stability: str
    generated_at: str


class FeedbackLoopMap:

    def __init__(self) -> None:
        self._loops: dict[str, FeedbackLoop] = {}
        self._amplification_paths: list[AmplificationPath] = []
        self._register_known_loops()
        self._register_amplification_paths()

    def _register_known_loops(self) -> None:
        loops = [
            FeedbackLoop(
                id="recall_access_boost",
                name="Recall → Access Count → Score Boost",
                status="active",
                severity="medium",
                path=[
                    "MemoryKernel.recall",
                    "score_candidates",
                    "_record_access",
                    "access_count",
                    "access_frequency_score",
                ],
                description=(
                    "Each recall boosts a record's access_count, which increases "
                    "its access_frequency score (weight 0.10), creating a "
                    "rich-get-richer effect where popular records dominate."
                ),
                existing_safeguards=[
                    "Low weight (10%) limits score contribution",
                    "Recency decay reduces stale record advantage",
                ],
                missing_safeguards=[
                    "No access count ceiling or saturation curve",
                    "No diversity sampling to surface cold records",
                ],
                amplification_factor=1.1,
                damping_recommendation="logarithmic_damping on access_frequency score",
            ),
            FeedbackLoop(
                id="rate_tracker_reemit",
                name="RateTracker → Bus → RateTracker",
                status="guarded",
                severity="medium",
                path=[
                    "SomaticSignalBus",
                    "RateTracker.handle",
                    "spike_detection",
                    "emit_ALERTNESS",
                    "SomaticSignalBus",
                ],
                description=(
                    "Signal arrives, RateTracker detects spike and emits ALERTNESS "
                    "back to bus. Source prefix guard prevents direct re-entry but "
                    "indirect amplification via other subscribers remains possible."
                ),
                existing_safeguards=[
                    "Source prefix guard: rate_tracker.* filtered",
                    "60s cooldown between emissions",
                ],
                missing_safeguards=[
                    "No generation depth tracking on derived signals",
                    "No global rate limiter across all emitters",
                ],
                amplification_factor=2.0,
                damping_recommendation="generation_decay with 0.5 per generation",
            ),
            FeedbackLoop(
                id="correlator_reemit",
                name="SignalCorrelator → Bus → SignalCorrelator",
                status="guarded",
                severity="high",
                path=[
                    "SomaticSignalBus",
                    "SignalCorrelator._match_rule",
                    "compound_pattern",
                    "emit_synthesized",
                    "SomaticSignalBus",
                ],
                description=(
                    "Correlator detects compound pattern and emits synthesized signal. "
                    "Source prefix filter blocks direct re-entry but cross-amplification "
                    "with RateTracker can create indirect loops."
                ),
                existing_safeguards=[
                    "Source prefix filter: correlator.* excluded in _match_rule",
                    "Per-rule cooldown (60-180s)",
                ],
                missing_safeguards=[
                    "No cross-component amplification limit",
                    "No generation depth on synthesized signals",
                ],
                amplification_factor=2.5,
                damping_recommendation="generation_decay with 0.5 per generation",
            ),
            FeedbackLoop(
                id="anomaly_actuator",
                name="AnomalyEventStream → Actuators → Bus",
                status="latent",
                severity="high",
                path=[
                    "SomaticSignalBus",
                    "AnomalyEventStream",
                    "CognitiveResponse",
                    "actuator_action",
                    "new_signals",
                    "SomaticSignalBus",
                ],
                description=(
                    "AnomalyEventStream triggers CognitiveResponse actions (throttle, "
                    "escalate). System changes generate new signals that re-enter the "
                    "bus, creating slow oscillation under sustained pressure."
                ),
                existing_safeguards=[
                    "Per-rule cooldown (60-600s)",
                ],
                missing_safeguards=[
                    "No oscillation detection",
                    "No hysteresis on engage/disengage thresholds",
                    "No backpressure signal to upstream emitters",
                ],
                amplification_factor=3.0,
                damping_recommendation="hysteresis_gate with engage=0.7, release=0.4",
            ),
            FeedbackLoop(
                id="throttle_death_spiral",
                name="Throttle → Queue → Stress → Throttle",
                status="latent",
                severity="critical",
                path=[
                    "ThrottleController",
                    "task_queue_buildup",
                    "stress_scorer",
                    "elevated_queue_pressure",
                    "heavier_throttle",
                    "ThrottleController",
                ],
                description=(
                    "Heavy throttling causes task queue buildup. stress_scorer sees "
                    "elevated queue pressure and increases stress, leading to heavier "
                    "throttle. ThrottleLevel.HEAVY caps at 75% reduction but does not "
                    "break the cycle — a potential death spiral."
                ),
                existing_safeguards=[
                    "ThrottleLevel.HEAVY caps reduction at 75%",
                ],
                missing_safeguards=[
                    "No explicit backpressure or load-shedding",
                    "No queue depth circuit-breaker",
                    "No throttle-aware stress scoring adjustment",
                    "No sigmoid cap on stress-to-throttle mapping",
                ],
                amplification_factor=5.0,
                damping_recommendation="sigmoid_cap with midpoint=0.6, steepness=8.0",
            ),
        ]
        for loop in loops:
            self._loops[loop.id] = loop

    def _register_amplification_paths(self) -> None:
        self._amplification_paths = [
            AmplificationPath(
                id="env_to_anomaly_cascade",
                name="Environment → Correlator → RateTracker → AnomalyEventStream",
                source_loop="correlator_reemit",
                target_loop="anomaly_actuator",
                trigger_condition=(
                    "EnvironmentMonitor emits PRESSURE, correlator detects "
                    "system_distress and emits ALERTNESS, RateTracker detects "
                    "spike and emits another ALERTNESS"
                ),
                max_amplification=3.0,
                cooldown_protection="Per-component cooldowns (60-180s) but no global cascade limit",
            ),
            AmplificationPath(
                id="pain_to_bypass",
                name="PAIN → Correlator → REFLEX/CRITICAL bypass",
                source_loop="correlator_reemit",
                target_loop="anomaly_actuator",
                trigger_condition=(
                    "PAIN signal triggers correlator error_storm rule, emitting "
                    "REFLEX or CRITICAL which may invoke bypass_review response"
                ),
                max_amplification=2.0,
                cooldown_protection="Per-rule cooldown on error_storm but bypass has no rate limit",
            ),
        ]

    def get_all_loops(self) -> list[FeedbackLoop]:
        return list(self._loops.values())

    def get_by_status(self, status: str) -> list[FeedbackLoop]:
        return [l for l in self._loops.values() if l.status == status]

    def get_by_severity(self, severity: str) -> list[FeedbackLoop]:
        return [l for l in self._loops.values() if l.severity == severity]

    def get_loop(self, loop_id: str) -> FeedbackLoop | None:
        return self._loops.get(loop_id)

    def get_amplification_paths(self) -> list[AmplificationPath]:
        return list(self._amplification_paths)

    def generate_report(self) -> LoopMapReport:
        loops = self.get_all_loops()
        active = len(self.get_by_status("active"))
        guarded = len(self.get_by_status("guarded"))
        latent = len(self.get_by_status("latent"))
        max_amp = max((l.amplification_factor for l in loops), default=0.0)
        cross_paths = len(self._amplification_paths)

        if max_amp <= 2.0 and latent == 0:
            stability = "stable"
        elif max_amp <= 3.0:
            stability = "marginal"
        elif max_amp <= 5.0:
            stability = "degraded"
        else:
            stability = "unstable"

        return LoopMapReport(
            total_loops=len(loops),
            active=active,
            guarded=guarded,
            latent=latent,
            max_amplification=max_amp,
            cross_amplification_paths=cross_paths,
            overall_stability=stability,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
