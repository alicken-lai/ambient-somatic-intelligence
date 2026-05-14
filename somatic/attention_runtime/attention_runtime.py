"""
Somatic Attention Runtime — Unified attention processing pipeline.

Composes all Phase F components into a single runtime that processes
signals through a full pipeline:

  Signal → Normalize → Amplify → Prioritize → Score Stress → Throttle → Update Attention

The runtime works WITH existing somatic components (SignalBus,
AttentionManager, SignalCorrelator, etc.) rather than replacing them.
State snapshots are persisted to state/somatic_attention_snapshots/.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType, SignalUrgency
from somatic.attention_manager import AttentionManager
from somatic.attention_runtime.attention_engine import AttentionWeightingEngine
from somatic.attention_runtime.anomaly_amplifier import AnomalyAmplifier
from somatic.attention_runtime.signal_prioritizer import SignalPrioritizer
from somatic.attention_runtime.execution_throttle import AdaptiveExecutionThrottle, ThrottleState
from somatic.attention_runtime.stress_scorer import RuntimeStressScorer, StressScore

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
SNAPSHOT_DIR = AMBIENT_ROOT / "state" / "somatic_attention_snapshots"


@dataclass
class AnomalyEscalationReport:
    """Report on anomalies requiring escalation."""
    escalated_signals: list[dict[str, Any]]
    total_anomalies: int
    escalation_rate: float
    top_sources: list[str]
    recommendations: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "escalated_signals": self.escalated_signals,
            "total_anomalies": self.total_anomalies,
            "escalation_rate": round(self.escalation_rate, 4),
            "top_sources": self.top_sources,
            "recommendations": self.recommendations,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


class SomaticAttentionRuntime:
    """
    Unified attention runtime composing all Phase F components.

    Processes signals through the full pipeline and maintains runtime
    state across all attention subsystems.

    Usage:
        bus = SomaticSignalBus()
        attention_mgr = AttentionManager(bus)

        runtime = SomaticAttentionRuntime(
            bus=bus,
            attention_manager=attention_mgr,
        )

        # Process a signal through the full pipeline
        runtime.process_signal(signal)

        # Query state
        attention = runtime.get_attention_state()
        stress = runtime.get_stress_state()
        throttle = runtime.get_throttle_state()

        # Save/restore state
        runtime.snapshot()
    """

    def __init__(
        self,
        bus: SomaticSignalBus,
        attention_manager: AttentionManager,
        signal_analytics: Any | None = None,
        environment_monitor: Any | None = None,
        rate_tracker: Any | None = None,
    ):
        self._bus = bus
        self._attention_manager = attention_manager

        self._engine = AttentionWeightingEngine(attention_manager, bus)
        self._amplifier = AnomalyAmplifier(bus)
        self._prioritizer = SignalPrioritizer()
        self._throttle = AdaptiveExecutionThrottle()
        self._stress_scorer = RuntimeStressScorer()

        if signal_analytics:
            self._stress_scorer.set_signal_analytics(signal_analytics)
        if environment_monitor:
            self._stress_scorer.set_environment_monitor(environment_monitor)
        if rate_tracker:
            self._stress_scorer.set_rate_tracker(rate_tracker)

        self._processed_count = 0
        self._escalated_signals: list[dict[str, Any]] = []
        self._max_escalated = 100
        self._anomaly_sources: dict[str, int] = {}

    def process_signal(self, signal: SomaticSignal) -> dict[str, Any]:
        """
        Process a signal through the full attention pipeline.

        Pipeline stages:
          1. Amplify — adjust severity based on context
          2. Prioritize — score and rank against other signals
          3. Score stress — update aggregate stress from all sources
          4. Evaluate throttle — determine execution adjustment
          5. Update attention — recompute attention weights

        Returns a dict summarizing what happened at each stage.
        """
        self._processed_count += 1

        stress = self._stress_scorer.compute_stress()

        amplified = self._amplifier.amplify(signal, context={
            "stress_level": stress.overall,
        })

        recent = self._bus.recent(seconds=120.0)
        all_signals = recent + [signal]
        prioritized = self._prioritizer.prioritize(all_signals)

        throttle_action = self._throttle.evaluate(
            stress_level=stress.overall,
            current_load=self._estimate_load(len(all_signals)),
        )

        weights = self._engine.compute_weights(all_signals)
        self._prioritizer.set_attention_weights(weights)

        if amplified.amplified_severity > 0.7 or signal.is_critical:
            self._track_escalation(signal, amplified.amplified_severity)

        my_priority = next(
            (p for p in prioritized if p.signal is signal),
            None,
        )
        priority_score = my_priority.priority_score if my_priority else 0.0

        result = {
            "signal_type": signal.type.value,
            "original_urgency": signal.urgency.value,
            "amplified_severity": round(amplified.amplified_severity, 4),
            "amplification_factor": round(amplified.amplification_factor, 4),
            "priority_score": round(priority_score, 4),
            "stress_level": round(stress.overall, 4),
            "stress_class": stress.level.value,
            "throttle_level": throttle_action.level.name,
            "parallelism_factor": throttle_action.parallelism_factor,
            "processed_count": self._processed_count,
        }

        logger.debug(
            "Signal processed: type=%s amplified=%.3f priority=%.3f "
            "stress=%s throttle=%s",
            signal.type.value, amplified.amplified_severity,
            priority_score, stress.level.value, throttle_action.level.name,
        )
        return result

    def get_attention_state(self) -> dict[str, Any]:
        """Get current attention state snapshot."""
        profile = self._engine.get_attention_profile()
        mgr_state = self._attention_manager.current_state()
        return {
            "profile": profile.to_dict(),
            "attention_level": mgr_state.level.label,
            "max_concurrency": mgr_state.max_concurrency,
            "context_budget_ratio": mgr_state.context_budget_ratio,
            "governance_sensitivity": mgr_state.governance_sensitivity,
        }

    def get_stress_state(self) -> dict[str, Any]:
        """Get current stress state."""
        stress = self._stress_scorer.compute_stress()
        stress_map = self._stress_scorer.get_stress_map()
        return {
            "score": stress.to_dict(),
            "map": stress_map.to_dict(),
        }

    def get_throttle_state(self) -> dict[str, Any]:
        """Get current throttle state."""
        return self._throttle.get_throttle_state().to_dict()

    def snapshot(self) -> Path:
        """
        Save full attention runtime state to disk.

        Returns the path where the snapshot was saved.
        """
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

        profile = self._engine.get_attention_profile()
        mgr_state = self._attention_manager.current_state()
        throttle = self._throttle.get_throttle_state()

        stress_data: dict[str, Any] = {}
        try:
            stress = self._stress_scorer.compute_stress()
            stress_data = stress.to_dict()
        except Exception:
            pass

        snapshot_data = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "processed_count": self._processed_count,
            "attention": {
                "profile": profile.to_dict(),
                "level": mgr_state.level.label,
                "active_signals": mgr_state.active_signals,
                "critical_signals": mgr_state.critical_signals,
            },
            "stress": stress_data,
            "throttle": throttle.to_dict(),
            "priority_queue_size": len(self._prioritizer.get_priority_queue()),
            "escalated_count": len(self._escalated_signals),
        }

        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        filepath = SNAPSHOT_DIR / f"attention_snapshot_{ts}.json"

        try:
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            logger.info("Attention runtime snapshot saved to %s", filepath)
        except OSError:
            logger.warning("Failed to save snapshot to %s", filepath)

        return filepath

    def get_anomaly_escalation_report(self) -> AnomalyEscalationReport:
        """Generate a report on anomalies requiring escalation."""
        total = self._processed_count
        escalated_count = len(self._escalated_signals)
        rate = escalated_count / total if total > 0 else 0.0

        top_sources = sorted(
            self._anomaly_sources, key=self._anomaly_sources.get, reverse=True,
        )[:5]

        recommendations = self._escalation_recommendations(
            escalated_count, rate, top_sources,
        )

        return AnomalyEscalationReport(
            escalated_signals=list(self._escalated_signals[-20:]),
            total_anomalies=escalated_count,
            escalation_rate=rate,
            top_sources=top_sources,
            recommendations=recommendations,
        )

    def set_task_queue_depth(self, depth: int) -> None:
        """Update the stress scorer with current task queue depth."""
        self._stress_scorer.set_task_queue_depth(depth)

    def set_governance_escalation_count(self, count: int) -> None:
        """Update governance escalation count for stress scoring."""
        self._stress_scorer.set_governance_escalation_count(count)

    def _track_escalation(self, signal: SomaticSignal, severity: float) -> None:
        """Track a signal that requires escalation."""
        entry = {
            "type": signal.type.value,
            "source": signal.source,
            "urgency": signal.urgency.value,
            "severity": round(severity, 4),
            "message": signal.message,
            "timestamp": datetime.fromtimestamp(
                signal.timestamp, tz=timezone.utc
            ).isoformat(),
        }

        self._escalated_signals.append(entry)
        if len(self._escalated_signals) > self._max_escalated:
            self._escalated_signals = self._escalated_signals[-self._max_escalated:]

        self._anomaly_sources[signal.source] = (
            self._anomaly_sources.get(signal.source, 0) + 1
        )

    @staticmethod
    def _estimate_load(signal_count: int) -> float:
        """Estimate current load from signal volume."""
        return min(signal_count / 30.0, 1.0)

    @staticmethod
    def _escalation_recommendations(
        count: int,
        rate: float,
        top_sources: list[str],
    ) -> list[str]:
        """Generate escalation recommendations."""
        recs: list[str] = []

        if rate > 0.3:
            recs.append(
                f"High escalation rate ({rate:.0%}) — review anomaly thresholds"
            )
        if count > 20:
            recs.append(
                f"{count} signals escalated — investigate root cause"
            )
        if top_sources:
            recs.append(
                f"Top escalation sources: {', '.join(top_sources[:3])}"
            )
        if not recs:
            recs.append("Escalation levels within normal parameters")

        return recs
