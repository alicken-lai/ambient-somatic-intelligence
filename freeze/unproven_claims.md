# Unproven Claims — Honest Assessment

**Frozen:** 2026-05-18  
**Purpose:** Prevent marketing language from outrunning evidence. If a claim is not listed in [`freeze/proven_capabilities.md`](proven_capabilities.md), assume it is unproven unless cited below as partially evidenced.

---

## Operational Maturity

| Claim | Status | Evidence / gap |
|-------|--------|----------------|
| **30-day operational drift stability** | **UNPROVEN** | Longest stable capture ~105h; `telemetry/maturation/drift_report.json` covers ~2.7 days |
| **7+ full circadian cycles validated** | **UNPROVEN** | P1.7D: 4.37 cycles, `INSUFFICIENT_DURATION` waiver |
| **Long-term circadian sensitivity adjustments** | **UNPROVEN** | P1 recommended +25% late_night; not validated over 7+ days production |
| **Weekend / weekday differentiation** | **UNPROVEN** | No weekend data in P1 window (`docs/releases/p16_reality_gate.md`) |

---

## Precursor & Incidents

| Claim | Status | Evidence / gap |
|-------|--------|----------------|
| **Precursor detection ≥0.60 historical union** | **UNPROVEN** | P1.7C: **0.56** — FAIL |
| **Multi-incident precursor validation** | **UNPROVEN** | 2 historical incidents; INC-001 insufficient; none in daemon window |
| **INC-001 pre-incident precursor detection** | **UNPROVEN** | 19 REAL records T−60m; `INSUFFICIENT_COVERAGE` |
| **Chronic memory saturation FP <30%** | **UNPROVEN** | P1: 92% FP rate; not re-validated to threshold |
| **10+ incidents for statistical precursor model** | **UNPROVEN** | P1 gate roadmap; not achieved |

---

## Continuity & Telemetry

| Claim | Status | Evidence / gap |
|-------|--------|----------------|
| **Historical union continuity ≥0.95** | **UNPROVEN** | Frozen **0.7712** — FAIL (`docs/releases/p17c_reality_gate.md`) |
| **Full 168h capture without bootstrap gaps** | **UNPROVEN** | day_01–02 max gaps 27,857s / 28,463s |
| **Backfill of bootstrap era to union 0.95** | **UNPROVEN** | Recommended in P1.7C; not executed at closeout |
| **Interpolation-free precursor for INC-001** | **UNPROVEN** | 8h+ blind spot; P1.6 interpolation explicitly rejected |

---

## Cognition & Production

| Claim | Status | Evidence / gap |
|-------|--------|----------------|
| **Production-scale deployment** | **UNPROVEN** | Experimental / operationally-usable classification only |
| **Reality Score ≥0.90 (highly reliable)** | **UNPROVEN** | Best frozen: 0.812 operational, 0.8015 historical |
| **Autonomous promotion without governance** | **UNPROVEN by design** | `docs/releases/v0.3.1_known_limitations.md` |
| **Salience fairness ≥0.85** | **UNPROVEN** | Frozen 0.73; somatic starvation documented P1 |
| **Missed instinct recall ≥0.85** | **UNPROVEN** | Frozen 0.72; 3 HIGH priority gaps in P1 |
| **Enforcement modules wired in production DMN** | **PARTIALLY UNPROVEN** | Modules exist; P1.5 notes audit-mode rollout required |

---

## Gate & Release

| Claim | Status | Evidence / gap |
|-------|--------|----------------|
| **v0.4 historical 6-criterion gate PASS** | **UNPROVEN** | FAIL 3/6 at P1.7C — LOCKED |
| **P1.7 +7d projections (0.8165)** | **UNPROVEN** | Labeled PROJECTION in `docs/releases/p17_unlock_gate.md` |
| **P1.6 conditional v0.4 without waiting** | **SUPERSEDED / NOT MET** | P1.7D operational path chosen instead |

---

## What We Can Say Without Overclaiming

- **Operational sensing** in the daemon-stable window met the **P1.7D operational contract** (5/5).
- **Synthetic ontology** is stable (0.9592 health, 382 tests).
- **Historical union** composite crossed **0.80** but **failed** three sub-criteria that matter for full unlock.
- **Bootstrap-era gaps** are permanent in the record; they are classified, not erased.

---

## Re-evaluation Triggers

Revisit unproven claims when:

1. ≥168h additional daemon-stable capture (circadian cycles)
2. New materialized day files after bootstrap backfill attempt
3. New true incidents with adequate T−60m coverage
4. Explicit v0.4 stabilization milestone sign-off per [`docs/releases/v04_inheritance_contract.md`](../docs/releases/v04_inheritance_contract.md)
