"""Integration Map — Structured documentation of all v0.4 integrations.

Provides a machine-readable and human-readable overview of:
  - All v0.4 subsystems and their roles
  - All v0.4 event contracts
  - All v0.4 bus connections
  - An ASCII integration diagram
  - Backward compatibility notes
"""

from __future__ import annotations

from typing import Any

from integration.v04_contracts import V04_SCHEMAS, V04_SCHEMA_MAP


def generate_integration_map() -> dict[str, Any]:
    """
    Generate a structured dict documenting all v0.4 integrations.

    Returns a dict with subsystems, contracts, connections, diagram, and
    backward compatibility notes.
    """
    return {
        "version": "v0.4",
        "subsystems": _subsystems(),
        "event_contracts": _event_contracts(),
        "bus_connections": _bus_connections(),
        "integration_diagram": _ascii_diagram(),
        "backward_compatibility": _backward_compat_notes(),
    }


def _subsystems() -> list[dict[str, str]]:
    return [
        {
            "name": "skills",
            "module": "skills/core/",
            "role": "Formal skill layer — typed schemas, registry, routing, validation",
            "key_classes": "SkillRegistry, SkillRouter, SkillValidator, SkillSchema",
        },
        {
            "name": "attention",
            "module": "attention/",
            "role": "Cross-domain salience scoring, novelty/weak-signal detection, priority allocation, escalation",
            "key_classes": "SalienceEngine, NoveltyDetector, WeakSignalDetector, PriorityAllocator, EscalationRouter",
        },
        {
            "name": "somatic_memory",
            "module": "memory/somatic/",
            "role": "Environmental episodic memory — episode storage, fingerprinting, similarity, precursor detection",
            "key_classes": "SomaticEpisodeStore, EnvironmentalSignature, PatternSimilarity, PrecursorMatcher",
        },
        {
            "name": "skillify",
            "module": "agents/skillify/",
            "role": "Automated skill discovery — observe workflows, mine patterns, generate/validate/register candidate skills",
            "key_classes": "WorkflowObserver, SkillifyPatternMiner, SkillCandidateGenerator, SkillRegistrationPipeline",
        },
    ]


def _event_contracts() -> list[dict[str, Any]]:
    return [
        {
            "name": s.name,
            "source": s.source_subsystem,
            "target": s.target_subsystem,
            "payload_type": s.payload_type,
            "mechanism": s.mechanism,
            "field_count": len(s.payload_fields),
            "description": s.description[:120],
        }
        for s in V04_SCHEMAS
    ]


def _bus_connections() -> list[dict[str, str]]:
    return [
        {
            "name": "somatic_to_salience",
            "source": "somatic.bus (on_any)",
            "target": "attention.SalienceEngine",
            "mechanism": "callback",
            "description": "Convert SomaticSignal → AttentionSignal, compute salience",
        },
        {
            "name": "escalation_to_audit",
            "source": "attention.EscalationRouter",
            "target": "governance.AuditLog",
            "mechanism": "monkey_patch (evaluate)",
            "description": "Log ESCALATE decisions to governance audit trail",
        },
        {
            "name": "skill_router_to_attention",
            "source": "skills.SkillRouter",
            "target": "attention.SalienceEngine",
            "mechanism": "monkey_patch (execute_with_fallback)",
            "description": "Notify attention on skill execution start/completion",
        },
        {
            "name": "episode_store_to_memory",
            "source": "memory.somatic.SomaticEpisodeStore",
            "target": "memory.MemoryKernel",
            "mechanism": "monkey_patch (store)",
            "description": "Bridge high/critical somatic episodes to memory kernel",
        },
        {
            "name": "precursor_to_attention",
            "source": "memory.somatic.PrecursorMatcher",
            "target": "attention.SalienceEngine",
            "mechanism": "monkey_patch (match)",
            "description": "High-confidence precursor matches → attention signal",
        },
        {
            "name": "registration_to_governance",
            "source": "agents.skillify.SkillRegistrationPipeline",
            "target": "governance.AuditLog",
            "mechanism": "monkey_patch (propose)",
            "description": "Skill proposals logged and routed to governance review",
        },
        {
            "name": "observer_to_miner",
            "source": "agents.skillify.WorkflowObserver",
            "target": "agents.skillify.SkillifyPatternMiner",
            "mechanism": "monkey_patch (observe)",
            "description": "Feed workflow observations to pattern miner periodically",
        },
    ]


def _ascii_diagram() -> str:
    return """\
╔══════════════════════════════════════════════════════════════════════════╗
║                    Ambient OS v0.4 Integration Map                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌─────────────┐        ┌──────────────────┐        ┌──────────────┐   ║
║  │   Skills     │◄──────│    Attention      │───────►│  Governance  │   ║
║  │  Registry    │        │  SalienceEngine   │        │  AuditLog    │   ║
║  │  Router      │        │  EscalationRouter │        │  PolicyEngine│   ║
║  │  Validator   │        │  NoveltyDetector  │        │              │   ║
║  └──────┬───────┘        │  WeakSignalDet.   │        └──────┬───────┘   ║
║         │                │  PriorityAllocator│               │           ║
║         │                └────────┬──────────┘               │           ║
║         │                         │                          │           ║
║         │    ┌────────────────────┼──────────────────────┐   │           ║
║         │    │                    │                      │   │           ║
║         ▼    ▼                    ▼                      │   │           ║
║  ┌──────────────────┐   ┌──────────────────┐            │   │           ║
║  │  Somatic Memory  │   │  Somatic Signal  │            │   │           ║
║  │  EpisodeStore    │──►│  Bus (on_any)    │────────────┘   │           ║
║  │  PatternSimilar. │   │                  │                │           ║
║  │  PrecursorMatcher│   └──────────────────┘                │           ║
║  └──────┬───────────┘                                       │           ║
║         │                                                   │           ║
║         ▼                                                   │           ║
║  ┌──────────────────┐                                       │           ║
║  │  Memory Kernel   │                                       │           ║
║  │  (6-layer store) │                                       │           ║
║  └──────────────────┘                                       │           ║
║                                                             │           ║
║  ┌──────────────────┐                                       │           ║
║  │  Skillify        │───────────────────────────────────────┘           ║
║  │  Observer        │                                                   ║
║  │  PatternMiner    │──► SkillCandidateGenerator ──► RegistrationPipeline║
║  └──────────────────┘                                                   ║
║                                                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Connections (7):                                                      ║
║  ① SomaticBus.on_any ──────────► SalienceEngine (callback)            ║
║  ② EscalationRouter.evaluate ──► AuditLog (monkey_patch)              ║
║  ③ SkillRouter.execute ────────► SalienceEngine (monkey_patch)         ║
║  ④ EpisodeStore.store ─────────► MemoryKernel (monkey_patch)          ║
║  ⑤ PrecursorMatcher.match ────► SalienceEngine (monkey_patch)         ║
║  ⑥ RegistrationPipeline.propose► AuditLog (monkey_patch)              ║
║  ⑦ WorkflowObserver.observe ──► PatternMiner (monkey_patch)           ║
╚══════════════════════════════════════════════════════════════════════════╝"""


def _backward_compat_notes() -> list[str]:
    return [
        "v0.2 IntegrationBus.wire() connections are unmodified and remain active.",
        "v0.3 IntegrationBus.wire_v03() connections are unmodified and remain active.",
        "v0.4 skills/attention wiring does NOT modify kernel/__init__.py or kernel/bootstrap.py.",
        "v0.4 stabilization adds wire_v04() to kernel/integration_bus.py (additive, idempotent).",
        "v0.4 boot is additive — call boot_v04(kernel) after boot() and boot_v03().",
        "v0.4 wiring uses the same _log_event() method on IntegrationBus for consistent event logging.",
        "v0.4 event schemas extend EventSchemaRegistry; v0.2/v0.3 schemas remain intact.",
        "All v0.4 connections use try/except — partial failures do not block other connections.",
        "The SomaticSignalBus.on_any callback is purely additive (no monkey-patching of bus.emit).",
        "SkillRouter.execute_with_fallback monkey-patch preserves the original method's contract.",
        "v0.3.1 ontology layer is purely additive — no v0.4 modules are modified.",
        "v0.3.1 boot_ontology() runs AFTER boot_v04() and does not interfere with existing wiring.",
    ]


# ══════════════════════════════════════════════════════════════════════════
# v0.3.1 — Somatic Metacognition Update: Ontology Integration Map
# ══════════════════════════════════════════════════════════════════════════


def generate_ontology_integration_map() -> dict[str, Any]:
    """
    Generate a structured dict documenting v0.3.1 ontology integrations.

    The ontology layer introduces a formal 4-tier memory hierarchy (L1–L4)
    with promotion/decay engines, governance doctrine, and observable
    confidence lifecycle.
    """
    return {
        "version": "v0.3.1-alpha",
        "codename": "Somatic Metacognition Update",
        "subsystems": _ontology_subsystems(),
        "connections": _ontology_connections(),
        "integration_diagram": _ontology_ascii_diagram(),
        "constraints": _ontology_constraints(),
    }


def _ontology_subsystems() -> list[dict[str, str]]:
    return [
        {
            "name": "memory_ontology",
            "module": "memory/ontology/",
            "role": "Formal 4-layer memory hierarchy (L1 Episodic → L2 Instinct → L3 Skill → L4 Strategic)",
            "key_classes": "MemoryLayer, LAYER_REGISTRY, PromotionEngine, DecayEngine, ConfidenceModel",
        },
        {
            "name": "somatic_ontology_bridge",
            "module": "memory/somatic/ontology_bridge.py",
            "role": "Maps somatic episodes/fingerprints/clusters/precursors to ontology layers",
            "key_classes": "SomaticOntologyBridge, OntologyMapping, PromotionCandidate",
        },
        {
            "name": "somatic_confidence_tracker",
            "module": "memory/somatic/confidence_tracker.py",
            "role": "Tracks confidence lifecycle for somatic-originated entries",
            "key_classes": "SomaticConfidenceTracker",
        },
        {
            "name": "governance_doctrine",
            "module": "governance/doctrine/",
            "role": "Independent verification doctrine — no self-certification for L2+",
            "key_classes": "ConfidenceValidator, VerificationRequest, VerificationResult, VerificationPolicy",
        },
        {
            "name": "skillify_doctrine",
            "module": "agents/skillify/doctrine/",
            "role": "Formalized evolution pipeline: observation → instinct → skill → strategy",
            "key_classes": "(markdown doctrine documents — no runtime classes)",
        },
    ]


def _ontology_connections() -> list[dict[str, str]]:
    return [
        {
            "name": "ontology_to_somatic_bridge",
            "source": "memory/ontology (schemas, layers)",
            "target": "memory/somatic/ontology_bridge.py",
            "mechanism": "import + composition",
            "description": "SomaticOntologyBridge maps SensorEpisode → L1, fingerprints → L2, clusters → L3, precursors → L4",
        },
        {
            "name": "ontology_to_governance_doctrine",
            "source": "memory/ontology (PromotionEngine)",
            "target": "governance/doctrine/confidence_validation.py",
            "mechanism": "import + policy check",
            "description": "ConfidenceValidator gates L2+ promotions; no self-certification allowed",
        },
        {
            "name": "ontology_to_skillify_pipeline",
            "source": "memory/ontology (PromotionCandidate)",
            "target": "agents/skillify/ (doctrine)",
            "mechanism": "promotion candidates as input",
            "description": "Skillify doctrine defines L1→L2→L3→L4 pipeline; ontology provides typed candidates",
        },
        {
            "name": "ontology_to_attention",
            "source": "memory/ontology (ConfidenceModel)",
            "target": "attention/ (SalienceEngine)",
            "mechanism": "confidence-weighted salience (planned)",
            "description": "Entry confidence feeds salience scoring — high-confidence entries get priority attention",
        },
        {
            "name": "ontology_to_observability",
            "source": "memory/ontology (DecayEngine reports)",
            "target": "observability/ (telemetry)",
            "mechanism": "decay reports as telemetry events (planned)",
            "description": "DecayEngine.generate_report() output can be emitted as telemetry for dashboards",
        },
    ]


def _ontology_ascii_diagram() -> str:
    return """\
╔══════════════════════════════════════════════════════════════════════════╗
║              Ambient OS v0.3.1 Ontology Integration Map                ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │                   Memory Ontology (memory/ontology/)              │  ║
║  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  ║
║  │  │L1 Episod.│─►│L2 Instinct│─►│L3 Skill  │─►│L4 Strategic     │ │  ║
║  │  │ (raw)    │  │ (atomic) │  │(workflow)│  │(heuristic/rule) │ │  ║
║  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │  ║
║  │       ▲              ▲              ▲                ▲           │  ║
║  │       │   Promotion  │   Promotion  │   Promotion    │           │  ║
║  │       │   Engine     │   Engine     │   Engine       │           │  ║
║  └───────┼──────────────┼──────────────┼────────────────┼───────────┘  ║
║          │              │              │                │              ║
║          │              │              │                │              ║
║  ┌───────┴──────┐ ┌─────┴─────────┐  ┌┴────────────┐  │              ║
║  │Somatic Bridge│ │Governance     │  │Skillify     │  │              ║
║  │(ontology_    │ │Doctrine       │  │Doctrine     │  │              ║
║  │ bridge.py)   │ │(confidence_   │  │(evolution   │  │              ║
║  │              │ │ validation.py)│  │ pipeline)   │  │              ║
║  └──────┬───────┘ └───────────────┘  └─────────────┘  │              ║
║         │                                              │              ║
║         ▼                                              │              ║
║  ┌──────────────┐                              ┌──────┴───────┐      ║
║  │Somatic Memory│                              │ Observability │      ║
║  │(episodes,    │                              │ (decay reports│      ║
║  │ fingerprints,│                              │  as telemetry)│      ║
║  │ clusters)    │                              └──────────────┘      ║
║  └──────────────┘                                                    ║
║                                                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Ontology Connections (5):                                            ║
║  ① OntologyBridge ─────────────► Somatic Memory (maps episodes)      ║
║  ② PromotionEngine ────────────► GovernanceDoctrine (gates L2+)      ║
║  ③ PromotionCandidate ─────────► Skillify Pipeline (typed input)     ║
║  ④ ConfidenceModel ────────────► Attention (weighted salience)       ║
║  ⑤ DecayEngine.report ─────────► Observability (telemetry)           ║
╚══════════════════════════════════════════════════════════════════════════╝"""


def _ontology_constraints() -> list[str]:
    return [
        "No auto-promotion: all L2+ promotions require governance approval.",
        "No self-certification: verifier_id must differ from implementer_id.",
        "All confidence changes are auditable via ConfidenceHistory.",
        "All promotions are reversible via PromotionEngine.rollback_promotion().",
        "Decay is observable: DecayEngine.generate_report() produces human-readable output.",
        "L4 Strategic promotion requires both governance_decision_id AND verifier_id.",
        "Full backward compatibility: no existing v0.4 modules are modified.",
    ]
