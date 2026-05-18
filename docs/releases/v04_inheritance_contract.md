# v0.4 Inheritance Contract — Stabilization Program

**Status:** ACTIVE (post P1 closeout)  
**Effective:** 2026-05-18  
**Predecessor freeze:** [`docs/releases/p1_reality_replay_program_closeout.md`](p1_reality_replay_program_closeout.md)  
**Doctrine:** [`docs/doctrine/bootstrap_gap_exception.md`](../doctrine/bootstrap_gap_exception.md)

---

## Purpose

Define what v0.4 stabilization **may** change vs what is **forbidden** after the P1 Reality Replay Program closeout. This contract inherits v0.3.1 architecture freeze ([`v0.3.1_architecture_freeze.md`](v0.3.1_architecture_freeze.md)) and P1 operational unlock ([`p17d_operational_unlock_gate.md`](p17d_operational_unlock_gate.md)).

---

## Inherited Baselines (Frozen Facts)

| Artifact | Value | Source |
|----------|-------|--------|
| Historical Reality Score | **0.8015** | P1.7C |
| Operational Reality Score | **0.812** | P1.7D |
| Historical union continuity | **0.7712** | P1.7C |
| Operational continuity | **1.0000** | P1.7D |
| Ontology health (synthetic) | **0.9592** | v0.3.1 release gate |
| Tests | **382/382** | v0.3.1 release gate |
| Daemon-stable window | 2026-05-13T15:00Z → 2026-05-17T23:59:13Z (~105h) | P1.7D |
| BOOTSTRAP_GAP count | **64** | P1.7D |
| DAEMON_FAILURE in stable window | **0** | P1.7D |

---

## ALLOWED in v0.4 Stabilization

### Operations & telemetry

- Continue and extend daemon-stable capture beyond 105h
- Automate daily maturation (`day_*.json`) from REAL sources
- Operational monitoring dashboards (historical vs operational scores labeled)
- Backfill **attempts** on day_01–02 with REAL sources only (syslog, dmesg, etc.) — results audited, not interpolated into official scores without governance review

### Integration & wiring

- Wire P1.5 enforcement modules into production mutation paths (with rollout flags)
- Deploy 5-minute sampling to all production DMN tick paths
- Execute retroactive memory migrations from P1.5 audit (DEMOTE, QUARANTINE, confidence correction)

### Testing & observability

- Add tests for `governance/`, `kernel/`, observability replay modules
- Expand integration tests for boot paths (`integration/v04_boot.py`, etc.)
- New observability metrics **that do not alter** frozen P1 reality score weights

### Documentation & freeze maintenance

- Append new gate reviews (P1.8, v0.4.x) — never delete P1 artifacts
- Update `freeze/` with new timestamps; preserve P1 closeout snapshot tags

### Scoring (constrained)

- **New** score versions (e.g., `p18_*`) with explicit `data_policy` and date
- Operational score recomputation on **extended** daemon windows
- Historical score recomputation after REAL backfill — must report delta vs frozen 0.8015

---

## FORBIDDEN in v0.4 Stabilization

### Reality program integrity

- **Modify** frozen P1 metric weights in `observability/replay/reality_score.py` (and matured variants) **without** a new numbered program phase and governance review
- **Retroactively change** published P1 scores (0.6645–0.812) in place — supersede only via new review IDs
- **Include INTERPOLATED** records in official P1.7+ REAL-only scores
- **Hide or delete** FAIL gate results, gap audits, or incident insufficient-coverage records

### Bootstrap doctrine violations

- Reclassify **DAEMON_FAILURE** as BOOTSTRAP_GAP without audit evidence
- Exclude bootstrap gaps from **historical union** denominator without documenting a new program phase
- Treat INC-001 insufficient coverage as operational precursor failure

### Architecture freeze violations

- Auto-promotion without governance (per v0.3.1)
- Self-certification for L2+ promotions
- Direct L4 strategy injection bypassing promotion chain
- Destructive memory edits violating append-only doctrine

### Release overclaim

- Claim **historical 6-criterion gate PASS** while continuity <0.95 or precursor <0.60
- Claim **production-ready** (≥0.95 reality) from operational 0.812 unlock
- Remove `INSUFFICIENT_DURATION` circadian caveat without ≥7 cycles evidence

---

## Dual-Gate Model (Required)

v0.4 work must report both:

| Gate | Closeout status | v0.4 goal |
|------|-----------------|-----------|
| **Historical (P1.7C)** | FAIL 3/6 LOCKED | Close gaps: continuity, precursor, circadian |
| **Operational (P1.7D)** | PASS 5/5 UNLOCKED | Maintain 0 DAEMON_FAILURE; extend duration |

---

## Success Criteria (v0.4 Stabilization — Aspirational)

Not met at P1 closeout; tracked as debt in [`freeze/technical_debt_register.md`](../../freeze/technical_debt_register.md):

1. Historical union continuity ≥ **0.95**
2. Historical precursor ≥ **0.60**
3. Historical circadian ≥ **0.70** without duration waiver
4. Enforcement modules verified on all production write paths
5. ≥ **168h** daemon-stable capture with automated materialization

---

## Cross-Links

- [`freeze/proven_capabilities.md`](../../freeze/proven_capabilities.md)
- [`freeze/unproven_claims.md`](../../freeze/unproven_claims.md)
- [`freeze/technical_debt_register.md`](../../freeze/technical_debt_register.md)
- [`v04_readiness_declaration.md`](v04_readiness_declaration.md)
