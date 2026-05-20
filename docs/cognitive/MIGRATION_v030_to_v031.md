# Migration Guide: v0.3.0-alpha → v0.3.1-alpha

**Codename:** Somatic Metacognition Update  
**Date:** 2026-05-14  
**Risk Level:** LOW (all changes are additive)

---

## What Changed

v0.3.1-alpha introduces a formal cognitive ontology — a 4-layer memory hierarchy
(L1 Episodic → L2 Instinct → L3 Skill → L4 Strategic) with promotion/decay
engines, governance doctrine, and observable confidence lifecycle.

**No existing runtime behavior is modified.** All changes are additive.

---

## New Directories Created

| Directory | Purpose |
|-----------|---------|
| `memory/ontology/` | Formal 4-layer memory hierarchy, schemas, promotion/decay engines |
| `governance/doctrine/` | Independent verification doctrine, confidence validation |
| `agents/skillify/doctrine/` | Formalized evolution pipeline documentation |
| `docs/cognitive/` | Specification documents for the ontology system |

---

## New Modules Added

### memory/ontology/
- `__init__.py` — Package exports
- `layer_definition.py` — `MemoryLayer` enum, `LayerDefinition`, `LAYER_REGISTRY`
- `episodic_schema.py` — `EpisodicEntry` (L1)
- `instinct_schema.py` — `InstinctEntry` (L2)
- `skill_schema.py` — `SkillMemoryEntry` (L3)
- `strategic_schema.py` — `StrategicEntry` (L4)
- `promotion_rules.py` — `PromotionRule`, `PROMOTION_RULES`, `check_promotion_eligibility()`
- `decay_rules.py` — `DecayRule`, `DECAY_RULES`, `DECAY_RULE_REGISTRY`, `compute_decay()`, `should_remove()`
- `confidence_model.py` — `ConfidenceModel`, `ConfidenceUpdate`, `ConfidenceHistory`
- `promotion_engine.py` — `PromotionEngine`, `PromotionCandidate`, `PromotionResult`
- `decay_engine.py` — `DecayEngine`, `DecayReport`

### memory/somatic/ (new files only)
- `ontology_bridge.py` — `SomaticOntologyBridge`, `OntologyMapping`
- `confidence_tracker.py` — `SomaticConfidenceTracker`
- `cluster_assignment.py` — `OntologyAwareClusterer`

### governance/doctrine/
- `independent_verification.md` — Doctrine specification
- `verifier_protocol.md` — Protocol for independent verifiers
- `confidence_validation.py` — `ConfidenceValidator`, `VerificationRequest`, `VerificationResult`

### agents/skillify/doctrine/
- `observation_to_instinct.md` — L1→L2 evolution documentation
- `instinct_to_skill.md` — L2→L3 evolution documentation
- `skill_to_strategy.md` — L3→L4 evolution documentation

### integration/
- `v031_boot.py` — `boot_ontology()`, `verify_ontology()`

### Tests
- `tests/test_ontology/` — 5 test files (65 tests)
- `tests/test_somatic_memory/test_ontology_bridge.py`
- `tests/test_somatic_memory/test_confidence_tracker.py`
- `tests/test_governance_doctrine/test_confidence_validation.py`
- `tests/test_integration/test_ontology_integration.py`
- `tests/test_integration/test_ontology_validation.py`

---

## Existing Modules Modified

Only **two** existing files have minimal modifications:

| File | Change |
|------|--------|
| `kernel/__init__.py` | `__version__` bumped from `"0.3.0-alpha"` to `"0.3.1-alpha"` |
| `integration/integration_map.py` | Added v0.3.1 ontology section (existing v0.4 content preserved) |

---

## How to Verify the Upgrade

```bash
# 1. Check version
python -c "from kernel import __version__; print(__version__)"
# Expected: 0.3.1-alpha

# 2. Run ontology verification
python -c "from integration.v031_boot import verify_ontology; print(verify_ontology())"
# Expected: all checks pass (True)

# 3. Run ontology boot
python -c "from integration.v031_boot import boot_ontology; r = boot_ontology(); print(r['_summary'])"
# Expected: all_passed: True

# 4. Run full test suite
python -m pytest tests/test_ontology/ tests/test_somatic_memory/ tests/test_governance_doctrine/ tests/test_integration/ -v
```

---

## What the Ontology Adds

### Formal L1–L4 Memory Hierarchy
- **L1 Episodic** — Raw sessions, logs, sensor events (30d retention, fastest decay)
- **L2 Instinct** — Atomic reusable observations distilled from patterns (180d retention)
- **L3 Skill** — Clustered workflows and reusable procedures (365d retention)
- **L4 Strategic** — Decision heuristics and metacognitive rules (unlimited retention)

### Promotion Engine
- Governance-gated knowledge promotion between layers
- No auto-promotion (governance required for L2+)
- Independent verification required for L3→L4
- All promotions are auditable and reversible

### Decay Engine
- Time-based exponential confidence decay per layer
- Inactivity-accelerated decay
- Contradiction and failure penalties
- Human-readable decay reports
- Entries are archived/removed when confidence falls below layer floor

### Governance Doctrine
- No self-certification (implementer ≠ verifier)
- Independent verification for L2+ promotions
- Verification expiry and re-verification triggers
- Full audit trail of all verification decisions

---

## Backward Compatibility Guarantees

1. All existing v0.2/v0.3/v0.4 subsystems remain unmodified
2. All existing integration bus wiring is preserved
3. All existing tests continue to pass without modification
4. The v0.4 boot sequence is not affected
5. No existing Python module paths change
6. No existing class/function signatures change
7. No existing enum values change

---

## Known Limitations

1. **Attention integration is planned but not wired** — confidence-weighted salience scoring is documented but not yet connected at runtime
2. **Observability integration is planned but not wired** — decay reports are generated but not yet emitted as telemetry events
3. **Somatic confidence tracker** uses in-memory storage only (no persistent backend yet)
4. **Ontology bridge** uses JSONL file for persistence (not integrated with MemoryKernel storage)
5. **No CLI commands** for ontology inspection (must use Python API directly)
