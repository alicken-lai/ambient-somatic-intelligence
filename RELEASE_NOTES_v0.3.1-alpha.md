# Release Notes — v0.3.1-alpha

**Version:** v0.3.1-alpha  
**Codename:** Somatic Metacognition Update  
**Date:** 2026-05-14  
**Backward Compatible:** Yes (fully additive)

---

## Summary

Introduces a formal cognitive ontology — a 4-layer memory hierarchy (L1–L4)
with promotion/decay engines, Guardian verification doctrine, and Skillify
evolution doctrine. All changes are additive; existing runtime is unmodified.

---

## What's New

### Memory Ontology Layer (`memory/ontology/`)
Formal 4-layer memory hierarchy with typed schemas, lifecycle management,
and governance-gated promotion between layers.

### Somatic Memory Ontology Integration
Bridges environmental episodes, anomaly fingerprints, episode clusters, and
precursor patterns to the formal L1–L4 cognitive hierarchy.

### Guardian Verification Doctrine (`governance/doctrine/`)
Independent verification protocol — no self-certification allowed. L2+
promotions require approval from an agent other than the implementer.

### Skillify Evolution Doctrine (`agents/skillify/doctrine/`)
Formalized L1→L2→L3→L4 knowledge promotion pipeline with explicit
criteria, governance gates, and documentation at each stage.

### Promotion Engine
Governance-gated knowledge promotion with full audit trail.
All promotions are proposed, approved, and reversible.

### Decay Engine
Observable confidence decay with time-based, inactivity, contradiction,
and failure penalties. Produces human-readable reports for observability.

### Confidence Model
Unified lifecycle authority for all confidence mutations with append-only
audit history and layer-specific floor enforcement.

---

## Architecture

```
L1 Episodic    — Raw sessions, logs, sensor events
                  Retention: 30d | Decay rate: 0.1/day | Max: 10,000 entries
                  
L2 Instinct    — Atomic reusable observations
                  Retention: 180d | Decay rate: 0.03/day | Max: 5,000 entries
                  Promotion requires: confidence ≥ 0.7, occurrences ≥ 3
                  
L3 Skill       — Clustered workflows, reusable procedures
                  Retention: 365d | Decay rate: 0.01/day | Max: 1,000 entries
                  Promotion requires: confidence ≥ 0.8, occurrences ≥ 5,
                  cross-context validation, governance approval
                  
L4 Strategic   — Decision heuristics, metacognitive rules
                  Retention: unlimited | Decay rate: 0.003/day | Max: 200 entries
                  Promotion requires: confidence ≥ 0.9, occurrences ≥ 10,
                  cross-context validation, governance approval, independent verifier
```

---

## Constraints

- **No auto-promotion** — All L2+ promotions require governance approval
- **No self-certification** — Independent verifier required (implementer ≠ verifier)
- **All changes observable** — ConfidenceHistory provides full audit trail
- **All changes auditable** — PromotionEngine.audit_log() records every decision
- **All changes reversible** — PromotionEngine.rollback_promotion() undoes approvals
- **Full backward compatibility** — No existing v0.3.0 modules are modified

---

## Files Modified (Existing)

| File | Change |
|------|--------|
| `kernel/__init__.py` | Version bump: `0.3.0-alpha` → `0.3.1-alpha` |
| `integration/integration_map.py` | Added v0.3.1 ontology integration section |

---

## New Test Coverage

- `tests/test_ontology/` — 65 unit tests for ontology internals
- `tests/test_somatic_memory/test_ontology_bridge.py` — Somatic bridge tests
- `tests/test_somatic_memory/test_confidence_tracker.py` — Confidence tracker tests
- `tests/test_governance_doctrine/test_confidence_validation.py` — Governance doctrine tests
- `tests/test_integration/test_ontology_integration.py` — Cross-system integration tests
- `tests/test_integration/test_ontology_validation.py` — Contract validation tests

---

## Migration

See [docs/cognitive/MIGRATION_v030_to_v031.md](docs/cognitive/MIGRATION_v030_to_v031.md)

## Rollback

See [docs/cognitive/ROLLBACK_v031.md](docs/cognitive/ROLLBACK_v031.md)

---

## Verification

```bash
# Quick verification
python -c "from integration.v031_boot import boot_ontology; r = boot_ontology(); assert r['_summary']['all_passed']"

# Full test suite
python -m pytest tests/ -v
```
