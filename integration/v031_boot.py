"""v0.3.1 boot sequence — Somatic Metacognition Update.

Additive boot layer that verifies the ontology subsystem is properly initialized.
Does NOT modify v0.4 boot — runs after it.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("integration.v031_boot")


def boot_ontology(kernel: Any = None) -> dict[str, Any]:
    """Boot the memory ontology subsystem.

    Returns dict with initialization status for each component.
    """
    start = time.monotonic()
    logger.info("v0.3.1 ontology boot sequence starting...")
    results: dict[str, Any] = {}

    # 1. Verify ontology layer definitions
    try:
        from memory.ontology.layer_definition import LAYER_REGISTRY, MemoryLayer
        assert len(LAYER_REGISTRY) == 4
        results["layer_definitions"] = {"status": "ok", "count": len(LAYER_REGISTRY)}
    except Exception as exc:
        results["layer_definitions"] = {"status": "error", "detail": str(exc)}

    # 2. Verify promotion rules are loaded
    try:
        from memory.ontology.promotion_rules import PROMOTION_RULES
        assert len(PROMOTION_RULES) == 3
        results["promotion_rules"] = {"status": "ok", "count": len(PROMOTION_RULES)}
    except Exception as exc:
        results["promotion_rules"] = {"status": "error", "detail": str(exc)}

    # 3. Verify decay rules are loaded
    try:
        from memory.ontology.decay_rules import DECAY_RULES
        assert len(DECAY_RULES) == 4
        results["decay_rules"] = {"status": "ok", "count": len(DECAY_RULES)}
    except Exception as exc:
        results["decay_rules"] = {"status": "error", "detail": str(exc)}

    # 4. Verify confidence model is initialized
    try:
        from memory.ontology.confidence_model import ConfidenceModel
        model = ConfidenceModel()
        assert model.history is not None
        results["confidence_model"] = {"status": "ok"}
    except Exception as exc:
        results["confidence_model"] = {"status": "error", "detail": str(exc)}

    # 5. Verify somatic bridge is connectable
    try:
        from memory.somatic.ontology_bridge import SomaticOntologyBridge
        results["somatic_bridge"] = {"status": "ok", "importable": True}
    except Exception as exc:
        results["somatic_bridge"] = {"status": "error", "detail": str(exc)}

    # 6. Verify governance doctrine validator is available
    try:
        from governance.doctrine.confidence_validation import ConfidenceValidator
        validator = ConfidenceValidator()
        assert callable(getattr(validator, "check_promotion_allowed", None))
        results["governance_doctrine"] = {"status": "ok"}
    except Exception as exc:
        results["governance_doctrine"] = {"status": "error", "detail": str(exc)}

    # 7. Verify all schemas are importable
    try:
        from memory.ontology.episodic_schema import EpisodicEntry
        from memory.ontology.instinct_schema import InstinctEntry
        from memory.ontology.skill_schema import SkillMemoryEntry
        from memory.ontology.strategic_schema import StrategicEntry
        results["schemas"] = {
            "status": "ok",
            "types": ["EpisodicEntry", "InstinctEntry", "SkillMemoryEntry", "StrategicEntry"],
        }
    except Exception as exc:
        results["schemas"] = {"status": "error", "detail": str(exc)}

    duration_ms = (time.monotonic() - start) * 1000
    ok_count = sum(1 for v in results.values() if v.get("status") == "ok")
    total = len(results)
    results["_summary"] = {
        "duration_ms": round(duration_ms, 1),
        "ok": ok_count,
        "total": total,
        "all_passed": ok_count == total,
    }

    logger.info(
        "v0.3.1 ontology boot complete in %.0fms — %d/%d checks passed",
        duration_ms, ok_count, total,
    )
    return results


def verify_ontology() -> dict[str, tuple[bool, str]]:
    """Verify ontology subsystem integrity.

    Returns dict mapping check_name → (passed, detail).
    """
    checks: dict[str, tuple[bool, str]] = {}

    # Check 1: All ontology modules importable
    try:
        import memory.ontology  # noqa: F401
        checks["modules_importable"] = (True, "memory.ontology package imports cleanly")
    except Exception as exc:
        checks["modules_importable"] = (False, str(exc))

    # Check 2: LAYER_REGISTRY has 4 entries
    try:
        from memory.ontology.layer_definition import LAYER_REGISTRY
        count = len(LAYER_REGISTRY)
        checks["layer_registry_count"] = (count == 4, f"LAYER_REGISTRY has {count} entries")
    except Exception as exc:
        checks["layer_registry_count"] = (False, str(exc))

    # Check 3: PROMOTION_RULES has 3 rules
    try:
        from memory.ontology.promotion_rules import PROMOTION_RULES
        count = len(PROMOTION_RULES)
        checks["promotion_rules_count"] = (count == 3, f"PROMOTION_RULES has {count} rules")
    except Exception as exc:
        checks["promotion_rules_count"] = (False, str(exc))

    # Check 4: DECAY_RULES has 4 rules
    try:
        from memory.ontology.decay_rules import DECAY_RULES
        count = len(DECAY_RULES)
        checks["decay_rules_count"] = (count == 4, f"DECAY_RULES has {count} rules")
    except Exception as exc:
        checks["decay_rules_count"] = (False, str(exc))

    # Check 5: Somatic bridge importable
    try:
        from memory.somatic.ontology_bridge import SomaticOntologyBridge  # noqa: F401
        checks["somatic_bridge"] = (True, "SomaticOntologyBridge importable")
    except Exception as exc:
        checks["somatic_bridge"] = (False, str(exc))

    # Check 6: Governance doctrine importable
    try:
        from governance.doctrine.confidence_validation import ConfidenceValidator  # noqa: F401
        checks["governance_doctrine"] = (True, "ConfidenceValidator importable")
    except Exception as exc:
        checks["governance_doctrine"] = (False, str(exc))

    # Check 7: Backward compat - existing memory/somatic still works
    try:
        from memory.somatic.sensor_episode_store import SomaticEpisodeStore  # noqa: F401
        checks["backward_compat_somatic"] = (True, "memory.somatic.SomaticEpisodeStore still works")
    except Exception as exc:
        checks["backward_compat_somatic"] = (False, str(exc))

    # Check 8: Backward compat - existing skills/ still works
    try:
        from skills.core.skill_registry import SkillRegistry  # noqa: F401
        checks["backward_compat_skills"] = (True, "skills.core.SkillRegistry still works")
    except Exception as exc:
        checks["backward_compat_skills"] = (False, str(exc))

    # Check 9: Backward compat - existing attention/ still works
    try:
        from attention.salience_engine import SalienceEngine  # noqa: F401
        checks["backward_compat_attention"] = (True, "attention.SalienceEngine still works")
    except Exception as exc:
        checks["backward_compat_attention"] = (False, str(exc))

    return checks
