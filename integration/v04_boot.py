"""v0.4 Boot Sequence — Initialise and wire all v0.4 subsystems.

Mirrors the pattern of kernel/bootstrap.py's boot_v03():
  1. Instantiate subsystems with try/except per subsystem
  2. Wire cross-subsystem connections
  3. Register default skills
  4. Return a typed container

Does NOT modify kernel/__init__.py, kernel/integration_bus.py, or
kernel/bootstrap.py — all v0.4 state lives in V04Subsystems.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel import AmbientKernel

from integration.v04_wiring import V04Wiring

logger = logging.getLogger("integration.v04_boot")


# ── V04 Subsystems Container ────────────────────────────────────────


@dataclass
class V04Subsystems:
    """Container for all v0.4 subsystem instances."""

    # skills
    skill_registry: Any = None
    skill_router: Any = None
    skill_validator: Any = None

    # attention
    salience_engine: Any = None
    novelty_detector: Any = None
    weak_signal_detector: Any = None
    priority_allocator: Any = None
    escalation_router: Any = None

    # somatic memory
    somatic_episode_store: Any = None
    environmental_signature: Any = None
    pattern_similarity: Any = None
    precursor_matcher: Any = None

    # skillify
    workflow_observer: Any = None
    pattern_miner: Any = None
    skill_candidate_generator: Any = None
    skill_registration_pipeline: Any = None

    # wiring state
    wiring: V04Wiring | None = None

    def subsystem_names(self) -> list[str]:
        """Return names of all subsystem slots (excluding wiring)."""
        return [
            f.name for f in self.__dataclass_fields__.values()
            if f.name != "wiring"
        ]

    def initialized_count(self) -> int:
        return sum(
            1 for name in self.subsystem_names()
            if getattr(self, name) is not None
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in self.subsystem_names():
            obj = getattr(self, name)
            result[name] = type(obj).__name__ if obj is not None else None
        result["wiring"] = self.wiring.status() if self.wiring else None
        return result


# ── Boot ─────────────────────────────────────────────────────────────


def boot_v04(kernel: "AmbientKernel") -> V04Subsystems:
    """
    Boot v0.4 subsystems on top of an already-booted v0.2/v0.3 kernel.

    Instantiates, wires, and registers default skills. All failures are
    caught per-subsystem so partial boot is possible.

    Args:
        kernel: A fully booted AmbientKernel instance.

    Returns:
        V04Subsystems container with all subsystem references.
    """
    start = time.monotonic()
    logger.info("v0.4 subsystem boot sequence starting...")

    v04 = V04Subsystems()

    # ── 1. Skills Layer ──────────────────────────────────────────────
    try:
        from skills.core.skill_registry import SkillRegistry
        from skills.core.skill_router import SkillRouter
        from skills.core.skill_validator import SkillValidator

        v04.skill_validator = SkillValidator()
        v04.skill_registry = SkillRegistry(validator=v04.skill_validator)
        v04.skill_router = SkillRouter(v04.skill_registry)
        logger.info("  [v0.4] Skills layer initialized (registry + router + validator)")
    except Exception as exc:
        logger.warning("  [v0.4] Skills layer failed: %s", exc)

    # ── 2. Attention Layer ───────────────────────────────────────────
    try:
        from attention.salience_engine import SalienceEngine
        from attention.novelty_detector import NoveltyDetector
        from attention.weak_signal_detector import WeakSignalDetector
        from attention.priority_allocator import PriorityAllocator
        from attention.escalation_router import EscalationRouter

        v04.salience_engine = SalienceEngine()
        v04.novelty_detector = NoveltyDetector()
        v04.weak_signal_detector = WeakSignalDetector()
        v04.priority_allocator = PriorityAllocator()
        v04.escalation_router = EscalationRouter()
        logger.info("  [v0.4] Attention layer initialized (5 components)")
    except Exception as exc:
        logger.warning("  [v0.4] Attention layer failed: %s", exc)

    # ── 3. Somatic Memory Layer ──────────────────────────────────────
    try:
        from memory.somatic.sensor_episode_store import SomaticEpisodeStore
        from memory.somatic.environmental_signature import EnvironmentalSignature
        from memory.somatic.pattern_similarity import PatternSimilarity
        from memory.somatic.precursor_matcher import PrecursorMatcher

        v04.somatic_episode_store = SomaticEpisodeStore()
        v04.environmental_signature = EnvironmentalSignature
        v04.pattern_similarity = PatternSimilarity()
        v04.precursor_matcher = PrecursorMatcher()
        logger.info("  [v0.4] Somatic Memory layer initialized (4 components)")
    except Exception as exc:
        logger.warning("  [v0.4] Somatic Memory layer failed: %s", exc)

    # ── 4. Skillify Layer ────────────────────────────────────────────
    try:
        from agents.skillify.workflow_observer import WorkflowObserver
        from agents.skillify.pattern_miner import SkillifyPatternMiner
        from agents.skillify.skill_candidate_generator import SkillCandidateGenerator
        from agents.skillify.skill_registration_pipeline import SkillRegistrationPipeline

        v04.workflow_observer = WorkflowObserver()
        v04.pattern_miner = SkillifyPatternMiner()
        v04.skill_candidate_generator = SkillCandidateGenerator()
        v04.skill_registration_pipeline = SkillRegistrationPipeline()
        logger.info("  [v0.4] Skillify layer initialized (4 components)")
    except Exception as exc:
        logger.warning("  [v0.4] Skillify layer failed: %s", exc)

    # ── 5. Wire v0.4 connections ─────────────────────────────────────
    if kernel.integration_bus is not None:
        try:
            from integration.v04_wiring import wire_v04

            v04.wiring = wire_v04(kernel, kernel.integration_bus, v04)
            logger.info("  [v0.4] Wiring complete (%d connections)", len(v04.wiring.connections))
        except Exception as exc:
            logger.warning("  [v0.4] Wiring failed: %s", exc)

    # ── 6. Register default skills ───────────────────────────────────
    if v04.skill_registry is not None:
        _register_default_skills(v04.skill_registry)

    # ── 7. Register v0.4 event schemas ───────────────────────────────
    try:
        from integration.v04_contracts import V04_SCHEMAS
        from architecture.bus_decomposition.event_schema import EventSchemaRegistry

        schema_registry = EventSchemaRegistry()
        for schema in V04_SCHEMAS:
            schema_registry._schemas[schema.name] = schema
        logger.info("  [v0.4] %d event schemas registered", len(V04_SCHEMAS))
    except Exception as exc:
        logger.warning("  [v0.4] Event schema registration failed: %s", exc)

    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "v0.4 subsystem boot complete in %.0fms — %d/%d subsystems initialized",
        duration_ms, v04.initialized_count(), len(v04.subsystem_names()),
    )
    return v04


def _register_default_skills(registry: Any) -> None:
    """Register built-in skills from skills/system, sensing, cognition, governance."""
    skill_modules: list[tuple[str, str]] = [
        ("skills.system", "memory_enrich_skill"),
        ("skills.system", "timeline_update_skill"),
        ("skills.system", "anomaly_explain_skill"),
        ("skills.sensing", "thermal_anomaly_detect_skill"),
        ("skills.cognition", "reflection_summarize_skill"),
        ("skills.governance", "risk_escalation_skill"),
        ("skills.governance", "approval_packet_skill"),
    ]

    registered = 0
    for module_path, skill_name in skill_modules:
        try:
            import importlib
            mod = importlib.import_module(module_path)
            skill = getattr(mod, skill_name, None)
            if skill is not None:
                registry.register(skill)
                registered += 1
                logger.debug("  Registered default skill: %s.%s", module_path, skill_name)
        except Exception as exc:
            logger.debug("  Failed to register %s.%s: %s", module_path, skill_name, exc)

    logger.info("  [v0.4] Registered %d/%d default skills", registered, len(skill_modules))


# ── Verify ───────────────────────────────────────────────────────────


def verify_v04(
    kernel: "AmbientKernel",
    v04: V04Subsystems,
) -> list[tuple[str, bool, str]]:
    """
    Post-boot verification for v0.4 subsystems.

    Returns a list of (check_name, passed, detail) tuples.
    """
    checks: list[tuple[str, bool, str]] = []

    # Check all subsystems are initialized
    subsystem_checks = {
        "skill_registry": lambda: v04.skill_registry is not None and callable(getattr(v04.skill_registry, "register", None)),
        "skill_router": lambda: v04.skill_router is not None and callable(getattr(v04.skill_router, "route", None)),
        "skill_validator": lambda: v04.skill_validator is not None and callable(getattr(v04.skill_validator, "validate_schema", None)),
        "salience_engine": lambda: v04.salience_engine is not None and callable(getattr(v04.salience_engine, "compute_salience", None)),
        "novelty_detector": lambda: v04.novelty_detector is not None,
        "weak_signal_detector": lambda: v04.weak_signal_detector is not None,
        "priority_allocator": lambda: v04.priority_allocator is not None,
        "escalation_router": lambda: v04.escalation_router is not None and callable(getattr(v04.escalation_router, "evaluate", None)),
        "somatic_episode_store": lambda: v04.somatic_episode_store is not None and callable(getattr(v04.somatic_episode_store, "store", None)),
        "pattern_similarity": lambda: v04.pattern_similarity is not None,
        "precursor_matcher": lambda: v04.precursor_matcher is not None and callable(getattr(v04.precursor_matcher, "match", None)),
        "workflow_observer": lambda: v04.workflow_observer is not None and callable(getattr(v04.workflow_observer, "observe", None)),
        "pattern_miner": lambda: v04.pattern_miner is not None and callable(getattr(v04.pattern_miner, "mine", None)),
        "skill_candidate_generator": lambda: v04.skill_candidate_generator is not None,
        "skill_registration_pipeline": lambda: v04.skill_registration_pipeline is not None and callable(getattr(v04.skill_registration_pipeline, "propose", None)),
    }

    for name, check_fn in subsystem_checks.items():
        try:
            passed = check_fn()
            detail = "initialized" if passed else "not initialized"
            checks.append((f"subsystem.{name}", passed, detail))
        except Exception as e:
            checks.append((f"subsystem.{name}", False, f"error: {e}"))

    # Check wiring
    if v04.wiring is not None:
        wiring_active = v04.wiring.is_active
        conn_count = len(v04.wiring.connections)
        checks.append((
            "wiring.active",
            wiring_active,
            f"{conn_count} connections" if wiring_active else "not active",
        ))

        expected_connections = {
            "somatic_to_salience",
            "escalation_to_audit",
            "skill_router_to_attention",
            "episode_store_to_memory",
            "precursor_to_attention",
            "registration_to_governance",
            "observer_to_miner",
        }
        active_connections = set(v04.wiring.connections)
        missing = expected_connections - active_connections
        checks.append((
            "wiring.completeness",
            len(missing) == 0,
            f"missing: {sorted(missing)}" if missing else "all 7 connections active",
        ))
    else:
        checks.append(("wiring.active", False, "no wiring object"))
        checks.append(("wiring.completeness", False, "no wiring object"))

    # Check default skills registered
    if v04.skill_registry is not None:
        try:
            all_skills = v04.skill_registry.list_all()
            skill_count = len(all_skills)
            checks.append((
                "default_skills.registered",
                skill_count >= 1,
                f"{skill_count} skills registered",
            ))
        except Exception as e:
            checks.append(("default_skills.registered", False, f"error: {e}"))
    else:
        checks.append(("default_skills.registered", False, "no registry"))

    # Check integration bus has v0.2 connections still active
    if kernel.integration_bus is not None:
        v02_ok = kernel.integration_bus.is_wired
        checks.append((
            "backward_compat.v02_wired",
            v02_ok,
            "v0.2 integration bus active" if v02_ok else "v0.2 bus NOT wired",
        ))
    else:
        checks.append(("backward_compat.v02_wired", False, "no integration bus"))

    return checks
