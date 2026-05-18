# Bootstrap Gap Exception Doctrine

**Status:** FROZEN (P1 closeout)  
**Effective:** 2026-05-18  
**Authority:** [`telemetry/maturation/p17d_continuity_exception_report.json`](../../telemetry/maturation/p17d_continuity_exception_report.json), [`docs/releases/p17d_operational_unlock_gate.md`](../releases/p17d_operational_unlock_gate.md)

---

## Purpose

Formalize how telemetry gaps are classified, scored, and reported so that **pre-daemon bootstrap sparsity** is not conflated with **operational sensing failure**, while **historical accountability** is preserved.

---

## Gap Classifications

### BOOTSTRAP_GAP

**Definition:** A telemetry gap that occurs entirely before the daemon-stable operational boundary (`2026-05-13T15:00:00+00:00`) and/or on Night-0 bootstrap days where no 5-minute union sampling contract existed.

**P1.7D evidence:** 64 gaps classified BOOTSTRAP_GAP; all end before or at pre-stable capture patterns on 2026-05-11 through 2026-05-13T10:22Z.

**Rationale examples (from audit):**
- Pre-daemon startup/init on 2026-05-11
- 7.7h / 7.9h sparse windows on day_01 / day_02 before stable cadence
- Pre-stable sub-hour gaps on 2026-05-12–13 while cadence was still forming

### DAEMON_FAILURE

**Definition:** A gap >10 minutes **inside** the daemon-stable window caused by daemon crash, launchd failure, or tick pipeline halt.

**P1.7D evidence:** **0** DAEMON_FAILURE gaps in stable window (`2026-05-13T15:00:00Z` → `2026-05-17T23:59:13Z`).

**Operational gate:** Criterion requires 0 DAEMON_FAILURE gaps >10 min — **PASS**.

### SOURCE_SILENCE

**Definition:** Expected absence of records from a registered source (e.g., optional sensor, disabled subsystem) with documented policy — distinct from system failure.

**P1.7D evidence:** Not used in current audit (0 classified).

### CLOCK_DRIFT

**Definition:** Gap or duplicate pattern caused by clock skew, NTP step, or timestamp validation failure per `telemetry/core/timestamp_validator.py`.

**P1.7D evidence:** Not used in current audit (0 classified).

### UNKNOWN

**Definition:** Gap that cannot be attributed after audit. Must be investigated before operational PASS.

**Rule:** UNKNOWN gaps **block** operational unlock until reclassified.

---

## Treatment Rules

### Historical (union) evaluation — P1.7C

| Rule | Behavior |
|------|----------|
| Denominator | Full 7-day union window (day_01–day_07 REAL records) |
| BOOTSTRAP_GAP | **Included** in union continuity (0.7712) — lowers score honestly |
| Interpolation | **Forbidden** in scoring; 121 P1.6 backfill records **excluded** |
| Gate | 6 criteria; FAIL 3/6 at closeout (precursor, circadian, continuity) |
| v0.4 status | **LOCKED** on historical gate |

### Operational evaluation — P1.7D

| Rule | Behavior |
|------|----------|
| Window | `daemon_stable_start` → last materialized record in stable era |
| BOOTSTRAP_GAP | **Excluded from operational continuity denominator** only |
| BOOTSTRAP_GAP | **Retained in audit trail** — never deleted |
| DAEMON_FAILURE | **Fails** operational gate if any >10 min in window |
| Interpolation | **Forbidden** |
| Gate | 5 criteria; **PASS 5/5** at closeout |
| v0.4 status | **UNLOCKED** (operational) |

### INC-001 insufficient coverage

| Field | Value |
|-------|-------|
| Incident | INC-001 @ 2026-05-11T21:49:02Z |
| T−60m REAL records | **19** (threshold ≥60) |
| Status | `INSUFFICIENT_COVERAGE` |
| Operational precursor | **Excluded** from numerator (not scored as failure) |
| Historical audit | **Retained** — documents 8h+ bootstrap blind spot |

**Frozen statement:** Records cluster at t−0 health burst, not sustained pre-incident 5-min cadence (max inter-record gap 6s). This is **missing data**, not a false negative on detection.

---

## Prohibited Practices

The following are **never** permitted under this doctrine:

1. **Hide failures** — Do not remove gap records, incident entries, or FAIL gate results from reports.
2. **Delete historical reports** — Append-only audit; supersede with new review IDs only.
3. **Bootstrap-as-false-negative** — Do not penalize operational precursor/circadian for INC-001 bootstrap blindness in the operational window.
4. **Reclassify DAEMON_FAILURE as BOOTSTRAP_GAP** without governance review and evidence.
5. **Score INTERPOLATED records** in P1.7+ official reality scores (121 excluded per materialization audit).

---

## Waiver Paths

### Circadian INSUFFICIENT_DURATION

When `circadian_status = INSUFFICIENT_DURATION` (<7 full cycles in daemon window):

- Operational circadian may pass gate if score ≥0.70 **and** waiver documented (P1.7D: 0.71 at 4.37 cycles).
- **Frozen caveat:** Long-term circadian claims remain **unproven** — see [`freeze/unproven_claims.md`](../../freeze/unproven_claims.md).

---

## Implementation References (read-only at freeze)

| Component | Path |
|-----------|------|
| Gap audit source | `telemetry/maturation/p17d_continuity_exception_report.json` |
| Gap detector | `telemetry/core/gap_detector.py` |
| Materialization | `telemetry/maturation/p17c_materialize.py` |
| Operational analyzer | `telemetry/maturation/p17d_analyze.py` |
| Daemon window freeze | `freeze/daemon_stable_window.json` |

---

## Cross-Links

- [`freeze/daemon_window_report.md`](../../freeze/daemon_window_report.md)
- [`docs/releases/p17d_operational_unlock_gate.md`](../releases/p17d_operational_unlock_gate.md)
- [`docs/releases/v04_inheritance_contract.md`](../releases/v04_inheritance_contract.md)
