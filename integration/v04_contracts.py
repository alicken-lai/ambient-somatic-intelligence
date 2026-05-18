"""Typed event contracts for all v0.4 cross-subsystem integrations.

Extends the EventSchemaRegistry (architecture/bus_decomposition/event_schema.py)
with BusEventSchema entries for the 14 v0.4 event flows across skills,
attention, somatic memory, skillify, and governance.
"""

from __future__ import annotations

from architecture.bus_decomposition.event_schema import BusEventSchema, EventField


def _build_v04_schemas() -> list[BusEventSchema]:
    """Build all v0.4 typed event contracts."""
    return [
        # ── Skill ↔ Attention ──────────────────────────────────────────

        BusEventSchema(
            name="skill_execution_started",
            source_subsystem="skills.skill_router",
            target_subsystem="attention",
            payload_type="SkillExecutionStarted",
            description=(
                "Emitted when a skill begins execution. The attention layer "
                "tracks this as an active workload to adjust budgets."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("skill_id", "str", True, "ID of the executing skill"),
                EventField("skill_name", "str", True, "Human-readable skill name"),
                EventField("trace_id", "str", True, "Execution trace ID for correlation"),
                EventField("governance_level", "str", True, "Governance level of the skill"),
                EventField("task_description", "str", True, "Task description that triggered the skill"),
            ],
        ),
        BusEventSchema(
            name="skill_execution_completed",
            source_subsystem="skills.skill_router",
            target_subsystem="attention",
            payload_type="SkillExecutionCompleted",
            description=(
                "Emitted when a skill finishes execution. Attention releases "
                "the tracked workload and updates salience history."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("skill_id", "str", True, "ID of the completed skill"),
                EventField("skill_name", "str", True, "Human-readable skill name"),
                EventField("trace_id", "str", True, "Execution trace ID"),
                EventField("success", "bool", True, "Whether the skill succeeded"),
                EventField("execution_time_ms", "float", True, "Total execution time in ms"),
                EventField("confidence", "float", True, "Result confidence score"),
                EventField("error", "str", False, "Error message if failed"),
            ],
        ),
        BusEventSchema(
            name="attention_skill_recommendation",
            source_subsystem="attention.salience_engine",
            target_subsystem="skills.skill_router",
            payload_type="AttentionSkillRecommendation",
            description=(
                "Attention recommends a skill based on high-salience signals. "
                "The skill router may use this to proactively invoke skills."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("signal_id", "str", True, "ID of the triggering attention signal"),
                EventField("salience_total", "float", True, "Computed salience score"),
                EventField("recommended_task", "str", True, "Suggested task description for skill routing"),
                EventField("source_domain", "str", True, "Signal source domain"),
                EventField("signal_type", "str", True, "Signal type that triggered recommendation"),
            ],
        ),

        # ── Skill ↔ Somatic Memory ────────────────────────────────────

        BusEventSchema(
            name="skill_somatic_episode_created",
            source_subsystem="skills.skill_router",
            target_subsystem="memory.somatic.episode_store",
            payload_type="SkillSomaticEpisodeCreated",
            description=(
                "When a skill execution creates notable environmental context, "
                "a somatic episode is persisted for future pattern matching."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("skill_id", "str", True, "ID of the skill that ran"),
                EventField("skill_name", "str", True, "Skill name"),
                EventField("episode_id", "str", True, "ID of the created somatic episode"),
                EventField("trace_id", "str", True, "Execution trace ID"),
                EventField("severity", "str", True, "Episode severity level"),
            ],
        ),
        BusEventSchema(
            name="somatic_pattern_skill_trigger",
            source_subsystem="memory.somatic.precursor_matcher",
            target_subsystem="skills.skill_router",
            payload_type="SomaticPatternSkillTrigger",
            description=(
                "When a somatic precursor pattern matches, suggesting that a "
                "specific skill should run proactively to handle the predicted event."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("pattern_id", "str", True, "ID of the matched precursor pattern"),
                EventField("target_event_type", "str", True, "Predicted event type"),
                EventField("confidence", "float", True, "Pattern match confidence"),
                EventField("recommended_skill_name", "str", False, "Skill name to invoke (if known)"),
                EventField("avg_lead_time_seconds", "float", True, "Average lead time before event"),
            ],
        ),

        # ── Attention ↔ Somatic Signal Bus ─────────────────────────────

        BusEventSchema(
            name="somatic_signal_to_attention",
            source_subsystem="somatic.bus",
            target_subsystem="attention.salience_engine",
            payload_type="SomaticToAttentionBridge",
            description=(
                "Bridge converting SomaticSignal events into AttentionSignal "
                "representations and feeding them to the SalienceEngine."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("somatic_type", "str", True, "Original SomaticSignal type (pressure/pain/…)"),
                EventField("somatic_urgency", "int", True, "Original urgency level"),
                EventField("source", "str", True, "Signal source identifier"),
                EventField("raw_value", "float", True, "Normalised 0.0–1.0 value for AttentionSignal"),
                EventField("attention_signal_id", "str", True, "ID of the converted AttentionSignal"),
            ],
        ),
        BusEventSchema(
            name="attention_escalation_event",
            source_subsystem="attention.escalation_router",
            target_subsystem="governance.audit_log",
            payload_type="AttentionEscalationEvent",
            description=(
                "When the EscalationRouter decides to ESCALATE a signal, "
                "the decision is forwarded to the governance audit log."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("signal_id", "str", True, "Escalated signal ID"),
                EventField("action", "str", True, "Escalation action (escalate)"),
                EventField("target", "str", True, "Escalation target"),
                EventField("reason", "str", True, "Escalation reason"),
                EventField("governance_required", "bool", True, "Always True for escalations"),
                EventField("salience_total", "float", True, "Salience score at escalation time"),
            ],
        ),

        # ── Somatic Memory ↔ Memory Kernel ─────────────────────────────

        BusEventSchema(
            name="somatic_episode_stored",
            source_subsystem="memory.somatic.episode_store",
            target_subsystem="memory.kernel",
            payload_type="SomaticEpisodeStored",
            description=(
                "When a somatic episode is persisted to the episode store, "
                "a bridge record is also stored in the memory kernel for "
                "cross-layer recall."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("episode_id", "str", True, "Persisted episode ID"),
                EventField("signal_types", "list[str]", True, "Signal types captured in the episode"),
                EventField("severity", "str", True, "Episode severity level"),
                EventField("duration_seconds", "float", True, "Episode duration"),
                EventField("memory_record_id", "str", False, "Memory kernel record ID (if bridged)"),
            ],
        ),
        BusEventSchema(
            name="somatic_precursor_detected",
            source_subsystem="memory.somatic.precursor_matcher",
            target_subsystem="attention",
            payload_type="SomaticPrecursorDetected",
            description=(
                "When the PrecursorMatcher detects a pattern matching a known "
                "precursor, the match is forwarded to attention as a high-priority signal."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("pattern_id", "str", True, "Matched precursor pattern ID"),
                EventField("target_event_type", "str", True, "Predicted event type"),
                EventField("confidence", "float", True, "Match confidence"),
                EventField("support_count", "int", True, "Historical support count"),
                EventField("avg_lead_time_seconds", "float", True, "Average lead time before target event"),
            ],
        ),

        # ── Skillify ↔ Skill Registry ──────────────────────────────────

        BusEventSchema(
            name="skillify_candidate_proposed",
            source_subsystem="agents.skillify.registration_pipeline",
            target_subsystem="skills.skill_registry",
            payload_type="SkillCandidateProposed",
            description=(
                "A new candidate skill has been proposed by the Skillify agent. "
                "The candidate enters the governance review queue."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("candidate_id", "str", True, "Unique candidate identifier"),
                EventField("proposed_name", "str", True, "Proposed skill name"),
                EventField("proposed_version", "str", True, "Proposed version string"),
                EventField("governance_level", "str", True, "Required governance level"),
                EventField("confidence_range", "list[float]", True, "Expected confidence range"),
                EventField("source_patterns_count", "int", True, "Number of source patterns"),
            ],
        ),
        BusEventSchema(
            name="skillify_candidate_approved",
            source_subsystem="governance",
            target_subsystem="agents.skillify.registration_pipeline",
            payload_type="SkillCandidateApproved",
            description=(
                "Governance has approved a candidate skill for registration. "
                "The pipeline proceeds to register the skill in the registry."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("candidate_id", "str", True, "Approved candidate ID"),
                EventField("proposal_id", "str", True, "Governance proposal ID"),
                EventField("approved_by", "str", True, "Approver identifier"),
                EventField("approved_at", "str", True, "ISO timestamp of approval"),
            ],
        ),
        BusEventSchema(
            name="skillify_skill_registered",
            source_subsystem="agents.skillify.registration_pipeline",
            target_subsystem="skills.skill_registry",
            payload_type="SkillifySkillRegistered",
            description=(
                "A skillify candidate has been registered as an active skill. "
                "The skill is now available for routing."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("skill_id", "str", True, "Registered skill ID in the registry"),
                EventField("candidate_id", "str", True, "Original candidate ID"),
                EventField("skill_name", "str", True, "Registered skill name"),
                EventField("registered_at", "str", True, "ISO timestamp of registration"),
                EventField("reversible", "bool", True, "Whether registration can be rolled back"),
            ],
        ),

        # ── Skillify ↔ Governance ──────────────────────────────────────

        BusEventSchema(
            name="skillify_governance_review_requested",
            source_subsystem="agents.skillify.registration_pipeline",
            target_subsystem="governance.audit_log",
            payload_type="SkillifyGovernanceReviewRequest",
            description=(
                "The Skillify pipeline requests governance review of a candidate "
                "skill. Logged in the audit trail with full candidate details."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("candidate_id", "str", True, "Candidate under review"),
                EventField("proposed_name", "str", True, "Proposed skill name"),
                EventField("governance_level", "str", True, "Requested governance level"),
                EventField("proposal_id", "str", True, "Governance proposal ticket ID"),
                EventField("validation_passed", "bool", True, "Whether candidate passed validation"),
            ],
        ),
        BusEventSchema(
            name="skillify_governance_decision",
            source_subsystem="governance",
            target_subsystem="agents.skillify.registration_pipeline",
            payload_type="SkillifyGovernanceDecision",
            description=(
                "Governance decision (approve/reject) for a candidate skill. "
                "The pipeline uses this to proceed or abort registration."
            ),
            mechanism="callback",
            version="v0.4",
            is_bidirectional=False,
            payload_fields=[
                EventField("proposal_id", "str", True, "Governance proposal ticket ID"),
                EventField("candidate_id", "str", True, "Candidate that was reviewed"),
                EventField("decision", "str", True, "'approved' or 'rejected'"),
                EventField("decided_by", "str", True, "Decision-maker identifier"),
                EventField("reason", "str", True, "Decision rationale"),
                EventField("decided_at", "str", True, "ISO timestamp of decision"),
            ],
        ),
    ]


V04_SCHEMAS = _build_v04_schemas()

V04_SCHEMA_NAMES = [s.name for s in V04_SCHEMAS]

V04_SCHEMA_MAP: dict[str, BusEventSchema] = {s.name: s for s in V04_SCHEMAS}
