# Civilization Regression Report

**Audit date:** 2026-05-20  
**Command:**

```bash
python3 -m pytest tests/v070/ tests/v071/ tests/v072/ tests/v073/ tests/v074/ tests/v075/ tests/v076/ tests/v077/ tests/v065c/ tests/v065b/ tests/v065/ tests/v064/ tests/v063/ tests/v062/ tests/v061/ tests/v060/ -q --tb=no
```

## Result

| Metric | Value |
|--------|-------|
| **Passed** | 395 |
| **Failed** | 0 |
| **Duration** | ~11.3s |

## v07x test areas (per gate doc Phase 9)

Each `tests/v0xx/` contains 10 `test_*.py` modules covering: audit, bounded layer, core, drift/fragmentation, explainability, governor wiring, integrity guards, observability, provenance/lineage, score.

**Civilization regression: PASS**
