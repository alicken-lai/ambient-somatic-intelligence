from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from runtime.feedback_stabilizer.loop_map import FeedbackLoopMap
from runtime.feedback_stabilizer.loop_detector import LoopDetector
from runtime.feedback_stabilizer.amplification_control import AmplificationController

logger = logging.getLogger(__name__)


@dataclass
class LoopHealthStatus:
    loop_id: str
    name: str
    is_active: bool
    current_frequency: float
    damping_effective: bool
    risk_level: str


@dataclass
class AmplificationStatus:
    current_factor: float
    max_observed: float
    cascade_active: bool
    rate_limited_count: int


@dataclass
class OscillationStatus:
    detected: bool
    frequency: float | None
    amplitude: float | None
    affected_components: list[str]


@dataclass
class StabilityRecommendation:
    priority: str
    target: str
    action: str
    reason: str
    expected_improvement: float


@dataclass
class StabilityReport:
    stability_score: float
    level: str
    loop_health: list[LoopHealthStatus]
    amplification: AmplificationStatus
    oscillation: OscillationStatus
    recommendations: list[StabilityRecommendation]
    assessed_at: str


class StabilityMonitor:

    def __init__(
        self,
        loop_map: FeedbackLoopMap,
        detector: LoopDetector,
        controller: AmplificationController,
    ) -> None:
        self._loop_map = loop_map
        self._detector = detector
        self._controller = controller
        self._max_observed_amplification: float = 1.0

    def assess(self) -> StabilityReport:
        loop_health = self._assess_loop_health()
        amp_status = self._assess_amplification()
        osc_status = self._assess_oscillation()
        score = self._compute_stability_score(loop_health, amp_status, osc_status)
        recommendations = self.get_recommendations(loop_health, amp_status, osc_status)

        if score > 0.8:
            level = "stable"
        elif score > 0.5:
            level = "marginal"
        elif score > 0.3:
            level = "degraded"
        else:
            level = "unstable"

        return StabilityReport(
            stability_score=round(score, 3),
            level=level,
            loop_health=loop_health,
            amplification=amp_status,
            oscillation=osc_status,
            recommendations=recommendations,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )

    def _assess_loop_health(self) -> list[LoopHealthStatus]:
        statuses: list[LoopHealthStatus] = []
        detected = {dl.loop_id: dl for dl in self._detector.detect_loops()}

        for loop in self._loop_map.get_all_loops():
            is_active = any(
                loop.id in dl.loop_id for dl in detected.values()
            )
            freq = 0.0
            for dl in detected.values():
                if loop.id in dl.loop_id:
                    freq = max(freq, dl.frequency)

            has_safeguards = len(loop.existing_safeguards) > 0
            few_missing = len(loop.missing_safeguards) <= 1
            damping_effective = has_safeguards and (not is_active or few_missing)

            if loop.severity == "critical" and is_active:
                risk = "critical"
            elif loop.severity in ("critical", "high") and not damping_effective:
                risk = "high"
            elif is_active:
                risk = "medium"
            else:
                risk = "low"

            statuses.append(LoopHealthStatus(
                loop_id=loop.id,
                name=loop.name,
                is_active=is_active,
                current_frequency=freq,
                damping_effective=damping_effective,
                risk_level=risk,
            ))

        return statuses

    def _assess_amplification(self) -> AmplificationStatus:
        current = self._controller.get_current_amplification()
        self._max_observed_amplification = max(self._max_observed_amplification, current)
        cascade = self._controller.is_cascade_active()

        rates = self._controller.get_emission_rates()
        rate_limited = sum(1 for r in rates.values() if r >= 25.0)

        return AmplificationStatus(
            current_factor=round(current, 2),
            max_observed=round(self._max_observed_amplification, 2),
            cascade_active=cascade,
            rate_limited_count=rate_limited,
        )

    def _assess_oscillation(self) -> OscillationStatus:
        chains = self._detector.get_active_chains()
        if not chains:
            return OscillationStatus(
                detected=False,
                frequency=None,
                amplitude=None,
                affected_components=[],
            )

        oscillating_components: set[str] = set()
        max_freq = 0.0
        max_amp = 0.0

        for chain in chains:
            if chain.depth < 3:
                continue
            sources = [e.source for e in chain.events]
            unique = set(sources)
            if len(sources) > len(unique):
                oscillating_components.update(unique)
                if len(chain.events) >= 2:
                    duration = chain.events[-1].timestamp - chain.events[0].timestamp
                    if duration > 0:
                        freq = len(chain.events) / duration
                        max_freq = max(max_freq, freq)
                max_amp = max(max_amp, chain.total_amplification)

        if not oscillating_components:
            return OscillationStatus(
                detected=False,
                frequency=None,
                amplitude=None,
                affected_components=[],
            )

        return OscillationStatus(
            detected=True,
            frequency=round(max_freq, 3),
            amplitude=round(max_amp, 2),
            affected_components=sorted(oscillating_components),
        )

    def _compute_stability_score(
        self,
        loop_health: list[LoopHealthStatus],
        amp_status: AmplificationStatus,
        osc_status: OscillationStatus,
    ) -> float:
        score = 1.0

        for lh in loop_health:
            if lh.risk_level == "critical":
                score -= 0.3
            elif lh.risk_level == "high":
                score -= 0.15
            elif lh.risk_level == "medium":
                score -= 0.05

        if amp_status.current_factor > 3.0:
            score -= 0.2
        elif amp_status.current_factor > 2.0:
            score -= 0.1

        if amp_status.cascade_active:
            score -= 0.15

        if osc_status.detected:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def get_recommendations(
        self,
        loop_health: list[LoopHealthStatus] | None = None,
        amp_status: AmplificationStatus | None = None,
        osc_status: OscillationStatus | None = None,
    ) -> list[StabilityRecommendation]:
        if loop_health is None or amp_status is None or osc_status is None:
            loop_health = self._assess_loop_health()
            amp_status = self._assess_amplification()
            osc_status = self._assess_oscillation()

        recs: list[StabilityRecommendation] = []

        for lh in loop_health:
            loop = self._loop_map.get_loop(lh.loop_id)
            if loop is None:
                continue

            if lh.risk_level in ("critical", "high"):
                recs.append(StabilityRecommendation(
                    priority="high" if lh.risk_level == "critical" else "medium",
                    target=lh.loop_id,
                    action=loop.damping_recommendation,
                    reason=f"Loop '{lh.name}' has {lh.risk_level} risk, "
                           f"missing safeguards: {loop.missing_safeguards}",
                    expected_improvement=0.15 if lh.risk_level == "critical" else 0.10,
                ))

        if amp_status.current_factor > 2.0:
            recs.append(StabilityRecommendation(
                priority="high",
                target="global",
                action="Enable generation_decay across all signal emitters",
                reason=f"System amplification factor is {amp_status.current_factor:.1f}x",
                expected_improvement=0.15,
            ))

        if osc_status.detected:
            recs.append(StabilityRecommendation(
                priority="high",
                target="oscillation",
                action="Apply hysteresis_gate to affected feedback loops",
                reason=f"Oscillation detected across {osc_status.affected_components}",
                expected_improvement=0.20,
            ))

        recs.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r.priority, 3))
        return recs
