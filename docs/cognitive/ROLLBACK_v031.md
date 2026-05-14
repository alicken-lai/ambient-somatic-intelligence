# Rollback Guide: v0.3.1-alpha → v0.3.0-alpha

**Risk Assessment:** LOW  
**Reason:** All v0.3.1 changes are additive — no existing runtime or data is affected.

---

## Overview

Rolling back from v0.3.1 to v0.3.0 is safe because:
- No existing modules were modified (only version string + integration map addition)
- No existing data formats changed
- No existing APIs changed
- No existing tests were modified

---

## Step 1: Remove New Directories

```bash
rm -rf memory/ontology/
rm -rf governance/doctrine/
rm -rf agents/skillify/doctrine/
rm -rf docs/cognitive/
rm -rf tests/test_ontology/
rm -rf tests/test_governance_doctrine/
```

---

## Step 2: Remove New Files

```bash
# Somatic memory additions
rm -f memory/somatic/ontology_bridge.py
rm -f memory/somatic/confidence_tracker.py
rm -f memory/somatic/cluster_assignment.py

# Integration additions
rm -f integration/v031_boot.py

# Test additions
rm -f tests/test_somatic_memory/test_ontology_bridge.py
rm -f tests/test_somatic_memory/test_confidence_tracker.py
rm -f tests/test_integration/test_ontology_integration.py
rm -f tests/test_integration/test_ontology_validation.py

# Release notes
rm -f RELEASE_NOTES_v0.3.1-alpha.md
```

---

## Step 3: Revert Modified Files

### kernel/__init__.py

Change the version back:

```python
# FROM:
__version__ = "0.3.1-alpha"

# TO:
__version__ = "0.3.0-alpha"
```

### integration/integration_map.py

Remove the v0.3.1 ontology section that was added at the bottom of the file
(everything after the `_backward_compat_notes()` function's original return list).

Specifically, revert the two added lines in `_backward_compat_notes()`:
- Remove: `"v0.3.1 ontology layer is purely additive — no v0.4 modules are modified."`
- Remove: `"v0.3.1 boot_ontology() runs AFTER boot_v04() and does not interfere with existing wiring."`

Remove the entire `generate_ontology_integration_map()` function and all helper
functions below it (`_ontology_subsystems`, `_ontology_connections`,
`_ontology_ascii_diagram`, `_ontology_constraints`).

### memory/somatic/__init__.py

If new exports were added (SomaticOntologyBridge, SomaticConfidenceTracker),
remove those import lines and `__all__` entries.

---

## Step 4: Verify Rollback

```bash
# 1. Check version reverted
python -c "from kernel import __version__; print(__version__)"
# Expected: 0.3.0-alpha

# 2. Verify existing tests still pass
python -m pytest tests/test_integration/test_boot_check.py -v
python -m pytest tests/test_integration/test_backward_compat.py -v

# 3. Verify no import errors from removed modules
python -c "from kernel import AmbientKernel; print('OK')"
```

---

## What is NOT Affected by Rollback

| Component | Impact |
|-----------|--------|
| All existing runtime modules | NONE — unchanged |
| All existing data files | NONE — no format changes |
| All existing tests | NONE — pass identically |
| Integration bus wiring | NONE — v0.2/v0.3/v0.4 all intact |
| Memory Kernel storage | NONE — no schema changes |
| Somatic Signal Bus | NONE — no modifications |
| Governance Policy Engine | NONE — no modifications |
| Skills layer | NONE — no modifications |
| Attention layer | NONE — no modifications |
| Observability layer | NONE — no modifications |

---

## Data Cleanup (Optional)

If the ontology bridge was used and created mapping files:

```bash
rm -f memory/somatic/ontology_mappings.jsonl
```

This file is only created if `SomaticOntologyBridge` was instantiated during runtime.
It is safe to delete — no other subsystem reads from it.

---

## Emergency Rollback (Git)

If the project uses Git, the simplest rollback is:

```bash
git log --oneline  # Find the commit before v0.3.1 changes
git revert <v0.3.1-commit-hash>
```

Or to reset completely:

```bash
git checkout v0.3.0-alpha -- kernel/__init__.py integration/integration_map.py
git rm -rf memory/ontology/ governance/doctrine/ agents/skillify/doctrine/ docs/cognitive/
git commit -m "rollback: revert v0.3.1-alpha to v0.3.0-alpha"
```
