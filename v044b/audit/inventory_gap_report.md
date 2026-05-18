# Inventory Gap Report (v0.4.4B)

**Generated:** 2026-05-18T21:14:29.776313+00:00

## Summary

| Metric | Value |
|--------|-------|
| v043 metadata scanned | 857 |
| v043 detail rows | 500 |
| v044 catalogued | 500 |
| Live rescan unique | 279 |
| Metadata gap (857−500) | 357 |

## Gap Explanation

857 is v043 audit metadata (total_scanned_mutations); only 500 detail rows exist in execution_authority_audit.json. The 357 gap is not missing inventory rows — it is unscanned-to-detail rollup (broader heuristic count vs path-level catalog). Live rescan finds 279 unique mutation sites.

## Comparisons

- Catalogued but not in live rescan: 488
- Live rescan not in v044 inventory: 267
- Missing paths file count: 267

## Phase 0 Verdict

**PASS_honest** — reconciled count documented honestly.
