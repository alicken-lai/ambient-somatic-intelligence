"""v0.4 Integration Wiring — Cross-subsystem connections for skills,
attention, somatic memory, and skillify.

Follows the EXACT pattern established in kernel/integration_bus.py:
  - Each connection wrapped in try/except (fault-tolerant)
  - Success/failure logged per connection
  - Callbacks preferred over monkey-patches
  - All connections tracked in a list for status introspection

Usage (called by v04_boot.py):
    from integration.v04_wiring import wire_v04, unwire_v04
    connections = wire_v04(kernel, bus, v04)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel import AmbientKernel
    from kernel.integration_bus import IntegrationBus

logger = logging.getLogger("integration.v04_wiring")


class V04Wiring:
    """
    Manages all v0.4 cross-subsystem connections.

    Stateful object that tracks which connections are active and can
    unwire them cleanly. Follows the same logging and fault-tolerance
    conventions as IntegrationBus.
    """

    def __init__(self) -> None:
        self._connections: list[str] = []
        self._active = False

    @property
    def connections(self) -> list[str]:
        return list(self._connections)

    @property
    def is_active(self) -> bool:
        return self._active

    def status(self) -> dict[str, Any]:
        return {
            "active": self._active,
            "connection_count": len(self._connections),
            "connections": list(self._connections),
        }


def wire_v04(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
) -> V04Wiring:
    """
    Establish all v0.4 cross-subsystem connections.

    Args:
        kernel: Fully booted AmbientKernel (v0.2+).
        bus: The IntegrationBus instance for event logging.
        v04: V04Subsystems container with all v0.4 subsystem references.

    Returns:
        V04Wiring tracker with the list of active connections.
    """
    wiring = V04Wiring()

    # ── 1. SomaticSignalBus → attention.SalienceEngine ─────────────
    _wire_somatic_to_salience(kernel, bus, v04, wiring)

    # ── 2. attention.EscalationRouter → governance.AuditLog ────────
    _wire_escalation_to_audit(kernel, bus, v04, wiring)

    # ── 3. skills.SkillRouter → attention (start/end notifications) ─
    _wire_skill_router_to_attention(kernel, bus, v04, wiring)

    # ── 4. SomaticEpisodeStore → memory.MemoryKernel ───────────────
    _wire_episode_store_to_memory(kernel, bus, v04, wiring)

    # ── 5. PrecursorMatcher → attention ────────────────────────────
    _wire_precursor_to_attention(kernel, bus, v04, wiring)

    # ── 6. SkillRegistrationPipeline → governance ──────────────────
    _wire_registration_to_governance(kernel, bus, v04, wiring)

    # ── 7. WorkflowObserver → SkillifyPatternMiner ─────────────────
    _wire_observer_to_miner(kernel, bus, v04, wiring)

    wiring._active = True
    bus._log_event(
        "kernel", "all",
        "v04_wired",
        f"v0.4 integration bus connected ({len(wiring._connections)} connections)",
    )
    logger.info(
        "v0.4 wiring complete: %d connections active", len(wiring._connections),
    )
    return wiring


def unwire_v04(wiring: V04Wiring) -> None:
    """Mark v0.4 connections as inactive."""
    wiring._active = False
    logger.info(
        "v0.4 wiring deactivated (%d connections)", len(wiring._connections),
    )


# ══════════════════════════════════════════════════════════════════════
# Individual connection wiring functions
# ══════════════════════════════════════════════════════════════════════


def _wire_somatic_to_salience(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """SomaticSignalBus.on_any → convert to AttentionSignal → SalienceEngine."""
    try:
        from attention.attention_state import AttentionSignal, AttentionSnapshot

        salience_engine = v04.salience_engine
        somatic_bus = kernel.somatic.bus

        def on_somatic_signal(signal) -> None:
            try:
                raw = signal.value / 100.0 if signal.value > 1.0 else signal.value
                raw = max(0.0, min(1.0, raw))

                attn_signal = AttentionSignal(
                    source_domain="somatic",
                    signal_type=signal.type.value,
                    raw_value=raw,
                    metadata={
                        "somatic_source": signal.source,
                        "somatic_urgency": signal.urgency.value,
                        "somatic_message": signal.message[:200],
                    },
                    source_ref=f"somatic.bus:{signal.type.value}",
                )

                context = AttentionSnapshot()
                salience_engine.compute_salience(attn_signal, context)

                bus._log_event(
                    "somatic.bus",
                    "attention.salience_engine",
                    "somatic_signal_to_attention",
                    f"{signal.type.value} → AttentionSignal (raw={raw:.2f})",
                )
            except Exception as exc:
                logger.debug("Somatic→salience conversion failed: %s", exc)

        somatic_bus.on_any(on_somatic_signal)
        wiring._connections.append("somatic_to_salience")
        logger.info("  [v0.4] Wired: SomaticSignalBus → SalienceEngine")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire SomaticSignalBus → SalienceEngine: %s", exc)


def _wire_escalation_to_audit(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """EscalationRouter decisions → governance.AuditLog."""
    try:
        from attention.escalation_router import EscalationAction

        escalation_router = v04.escalation_router
        audit_log = kernel.governance.audit_log

        original_evaluate = escalation_router.evaluate

        def evaluate_with_audit(*args, **kwargs):
            decision = original_evaluate(*args, **kwargs)
            try:
                if decision.action == EscalationAction.ESCALATE:
                    audit_log.record_decision(
                        action=f"attention.escalation:{decision.signal_id[:12]}",
                        risk="REVIEW_REQUIRED",
                        reason=decision.reason[:300],
                        agent_id="attention.escalation_router",
                        matched_policies=["attention_escalation"],
                        validation_stages=[{
                            "name": "escalation_review",
                            "passed": False,
                            "risk": "REVIEW_REQUIRED",
                        }],
                    )
                    bus._log_event(
                        "attention.escalation_router",
                        "governance.audit_log",
                        "attention_escalation_event",
                        f"signal={decision.signal_id[:8]} → ESCALATE "
                        f"(salience={decision.salience_total:.3f})",
                    )
            except Exception as exc:
                logger.debug("Escalation→audit logging failed: %s", exc)
            return decision

        escalation_router.evaluate = evaluate_with_audit
        wiring._connections.append("escalation_to_audit")
        logger.info("  [v0.4] Wired: EscalationRouter → GovernanceAuditLog")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire EscalationRouter → AuditLog: %s", exc)


def _wire_skill_router_to_attention(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """SkillRouter.execute_with_fallback → attention notifications on start/end."""
    try:
        from attention.attention_state import AttentionSignal, AttentionSnapshot

        skill_router = v04.skill_router
        salience_engine = v04.salience_engine

        original_execute = skill_router.execute_with_fallback

        def execute_with_attention(decision, context, **kwargs):
            skill = decision.selected_skill
            if skill:
                try:
                    start_signal = AttentionSignal(
                        source_domain="skills",
                        signal_type="skill_execution_started",
                        raw_value=decision.confidence,
                        metadata={
                            "skill_id": skill.skill_id,
                            "skill_name": skill.name,
                            "trace_id": context.trace_id,
                        },
                        source_ref=f"skills.router:{skill.skill_id}",
                    )
                    salience_engine.compute_salience(
                        start_signal, AttentionSnapshot(),
                    )
                    bus._log_event(
                        "skills.skill_router",
                        "attention",
                        "skill_execution_started",
                        f"skill='{skill.name}' trace={context.trace_id[:8]}",
                    )
                except Exception as exc:
                    logger.debug("Skill start→attention failed: %s", exc)

            start_time = time.monotonic()
            result = original_execute(decision, context, **kwargs)

            if skill:
                try:
                    elapsed = (time.monotonic() - start_time) * 1000
                    end_signal = AttentionSignal(
                        source_domain="skills",
                        signal_type="skill_execution_completed",
                        raw_value=result.confidence if result.success else 0.0,
                        metadata={
                            "skill_id": skill.skill_id,
                            "skill_name": skill.name,
                            "trace_id": result.trace_id,
                            "success": result.success,
                            "execution_time_ms": elapsed,
                        },
                        source_ref=f"skills.router:{skill.skill_id}",
                    )
                    salience_engine.compute_salience(
                        end_signal, AttentionSnapshot(),
                    )
                    bus._log_event(
                        "skills.skill_router",
                        "attention",
                        "skill_execution_completed",
                        f"skill='{skill.name}' success={result.success} "
                        f"({elapsed:.0f}ms)",
                    )
                except Exception as exc:
                    logger.debug("Skill end→attention failed: %s", exc)

            return result

        skill_router.execute_with_fallback = execute_with_attention
        wiring._connections.append("skill_router_to_attention")
        logger.info("  [v0.4] Wired: SkillRouter → Attention (start/end)")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire SkillRouter → Attention: %s", exc)


def _wire_episode_store_to_memory(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """SomaticEpisodeStore.store → bridge significant episodes to MemoryKernel."""
    try:
        episode_store = v04.somatic_episode_store
        memory_kernel = kernel.memory

        original_store = episode_store.store

        def store_with_bridge(episode, **kwargs):
            result = original_store(episode, **kwargs)
            try:
                severity = getattr(episode, "severity", "low")
                if severity in ("high", "critical"):
                    memory_kernel.store(
                        layer="episodic",
                        content=f"[somatic-episode] {episode.episode_id}: {getattr(episode, 'summary', '')}",
                        tags=["somatic", "auto-bridged", severity],
                        metadata={
                            "source": "memory.somatic.episode_store",
                            "episode_id": episode.episode_id,
                            "signal_types": getattr(episode, "signal_types", []),
                        },
                    )
                    bus._log_event(
                        "memory.somatic.episode_store",
                        "memory.kernel",
                        "somatic_episode_stored",
                        f"episode={episode.episode_id[:8]} severity={severity} "
                        "→ bridged to memory kernel",
                    )
            except Exception as exc:
                logger.debug("Episode→memory bridge failed: %s", exc)
            return result

        episode_store.store = store_with_bridge
        wiring._connections.append("episode_store_to_memory")
        logger.info("  [v0.4] Wired: SomaticEpisodeStore → MemoryKernel")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire EpisodeStore → MemoryKernel: %s", exc)


def _wire_precursor_to_attention(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """PrecursorMatcher.match → AttentionSignal for high-confidence precursors."""
    try:
        from attention.attention_state import AttentionSignal, AttentionSnapshot

        precursor_matcher = v04.precursor_matcher
        salience_engine = v04.salience_engine

        original_match = precursor_matcher.match

        def match_with_attention(*args, **kwargs):
            matches = original_match(*args, **kwargs)
            for m in matches:
                try:
                    if m.confidence >= 0.5:
                        attn_signal = AttentionSignal(
                            source_domain="somatic_memory",
                            signal_type="precursor_detected",
                            raw_value=m.confidence,
                            metadata={
                                "pattern_id": m.pattern_id,
                                "target_event_type": m.target_event_type,
                                "support_count": m.support_count,
                                "avg_lead_time_seconds": m.avg_lead_time_seconds,
                                "governance_relevant": True,
                            },
                            source_ref=f"somatic.precursor:{m.pattern_id}",
                        )
                        salience_engine.compute_salience(
                            attn_signal, AttentionSnapshot(),
                        )
                        bus._log_event(
                            "memory.somatic.precursor_matcher",
                            "attention",
                            "somatic_precursor_detected",
                            f"pattern={m.pattern_id} target={m.target_event_type} "
                            f"confidence={m.confidence:.2f}",
                        )
                except Exception as exc:
                    logger.debug("Precursor→attention failed: %s", exc)
            return matches

        precursor_matcher.match = match_with_attention
        wiring._connections.append("precursor_to_attention")
        logger.info("  [v0.4] Wired: PrecursorMatcher → Attention")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire PrecursorMatcher → Attention: %s", exc)


def _wire_registration_to_governance(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """SkillRegistrationPipeline.propose → governance audit + review."""
    try:
        pipeline = v04.skill_registration_pipeline
        audit_log = kernel.governance.audit_log

        original_propose = pipeline.propose

        def propose_with_governance(candidate, **kwargs):
            result = original_propose(candidate, **kwargs)
            try:
                audit_log.record_decision(
                    action=f"skillify.propose:{candidate.candidate_id[:12]}",
                    risk="REVIEW_REQUIRED",
                    reason=(
                        f"Skillify proposes '{candidate.proposed_name}' v{candidate.proposed_version} "
                        f"(governance={candidate.governance_level})"
                    ),
                    agent_id="agents.skillify",
                    matched_policies=["skillify_governance"],
                    validation_stages=[{
                        "name": "skillify_proposal",
                        "passed": result.status == "pending_review",
                        "risk": "REVIEW_REQUIRED",
                    }],
                )
                bus._log_event(
                    "agents.skillify.registration_pipeline",
                    "governance.audit_log",
                    "skillify_governance_review_requested",
                    f"candidate='{candidate.proposed_name}' → proposal={result.proposal_id[:8]}",
                )
            except Exception as exc:
                logger.debug("Proposal→governance logging failed: %s", exc)
            return result

        pipeline.propose = propose_with_governance
        wiring._connections.append("registration_to_governance")
        logger.info("  [v0.4] Wired: SkillRegistrationPipeline → Governance")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire RegistrationPipeline → Governance: %s", exc)


def _wire_observer_to_miner(
    kernel: "AmbientKernel",
    bus: "IntegrationBus",
    v04: Any,
    wiring: V04Wiring,
) -> None:
    """WorkflowObserver.observe → feed events to SkillifyPatternMiner."""
    try:
        observer = v04.workflow_observer
        miner = v04.pattern_miner

        original_observe = observer.observe

        def observe_with_mining(event, **kwargs):
            result = original_observe(event, **kwargs)
            try:
                events = observer.recent(limit=50)
                if len(events) >= 5 and len(events) % 5 == 0:
                    miner.mine(events, min_support=3)
                    bus._log_event(
                        "agents.skillify.workflow_observer",
                        "agents.skillify.pattern_miner",
                        "workflow_events_mined",
                        f"Mined {len(events)} events for patterns",
                    )
            except Exception as exc:
                logger.debug("Observer→miner feeding failed: %s", exc)
            return result

        observer.observe = observe_with_mining
        wiring._connections.append("observer_to_miner")
        logger.info("  [v0.4] Wired: WorkflowObserver → PatternMiner")

    except Exception as exc:
        logger.warning("  [v0.4] Failed to wire Observer → PatternMiner: %s", exc)
