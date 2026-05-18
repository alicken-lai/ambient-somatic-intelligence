# Daemon-Stable Window — Narrative Snapshot

**Frozen:** 2026-05-18  
**JSON:** [`freeze/daemon_stable_window.json`](daemon_stable_window.json)  
**Source audit:** [`telemetry/maturation/p17d_continuity_exception_report.json`](../telemetry/maturation/p17d_continuity_exception_report.json)

---

## Window Definition

| Field | Value |
|-------|-------|
| **Start** | `2026-05-13T15:00:00+00:00` |
| **End** | `2026-05-17T23:59:13.138892+00:00` |
| **Duration** | **104.99 hours (~105h)** |
| **Boundary note** | 60s DMN ticks begin ~12:00Z May 13; 5-min union replay reaches 1.0 after 15:00Z |

This window is the **authoritative operational sensing era** for P1.7D unlock and v0.4 stabilization entry.

---

## Continuity

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Operational continuity | **1.0000** | 1260/1260 five-minute slots occupied |
| Max gap in window | ≤64s (per day_05–07 materialization) | No gap >10 min |
| DAEMON_FAILURE (>10 min) | **0** | Operational gate PASS |
| Historical union continuity | **0.7712** | Bootstrap era drags full 7-day union |

Methodology: `operational_occupied / (expected_slots - bootstrap_slot_ids)` — bootstrap intervals excluded from operational denominator only ([`docs/doctrine/bootstrap_gap_exception.md`](../docs/doctrine/bootstrap_gap_exception.md)).

---

## Gap Classification Summary

| Class | Count (stable-era relevant) | In-window >10 min |
|-------|----------------------------|-------------------|
| BOOTSTRAP_GAP | 64 (all pre-15:00Z May 13) | 0 inside stable window |
| DAEMON_FAILURE | 0 | 0 |
| SOURCE_SILENCE | 0 | — |
| CLOCK_DRIFT | 0 | — |
| UNKNOWN | 0 | — |

All 64 BOOTSTRAP_GAP entries are **documented** in `p17d_continuity_exception_report.json` (GAP-P17D-001 through GAP-P17D-064). They are **not hidden** and **not deleted**.

---

## Operational Cadence

From P1.7 drift analysis and P1.7C materialization (days 05–07):

- ~14,390 REAL records/day on May 15–17
- Max gap **63–64 seconds** (sub-minute, within 60s tick tolerance)
- Sources: `dmn.tick`, `checksums.log`, `actions.log`
- Coverage **~99.9%** per calendar day

Daemon-era event rate: **360 events/hour** steady-state (P1.7).

---

## Incidents vs Window

### INC-001 (outside window)

- **Time:** 2026-05-11T21:49:02Z (bootstrap day)
- **T−60m REAL records:** 19 (need ≥60)
- **Status:** `INSUFFICIENT_COVERAGE`
- **Impact:** Excluded from operational precursor scoring; remains in historical audit

### INC-002 (outside window)

- **Time:** 2026-05-11T22:14:37Z
- **T−60m REAL records:** 260
- **Status:** `ADEQUATE_COVERAGE` for burst analysis
- **Impact:** Historical precursor evidence only; not in daemon-stable operational numerator

**No incidents occurred inside the daemon-stable window** at closeout — operational precursor score (0.61) reflects infrastructure and covered-incident methodology, not multi-incident validation.

---

## Scores Computed on This Window

| Metric | Operational value |
|--------|-------------------|
| Reality Score | **0.812** |
| Precursor detection | **0.61** |
| Circadian adaptation | **0.71** (INSUFFICIENT_DURATION — 4.37 cycles) |
| Continuity | **1.00** |

Gate: **PASS 5/5** — [`docs/releases/p17d_operational_unlock_gate.md`](../docs/releases/p17d_operational_unlock_gate.md).

---

## What This Window Does Not Prove

- 30-day operational drift stability
- Multi-incident precursor validation
- Full 7-day circadian cycles (need ≥168h continuous for waiver removal)
- Historical union continuity ≥0.95

See [`freeze/unproven_claims.md`](unproven_claims.md).

---

## Monitoring References

- Daemon health: `state/daemon/dmn_tick_status.json`
- Day files: `telemetry/maturation/day_05.json` – `day_07.json`
- Live logs: `logs/actions.jsonl`, `memory/dmn.jsonl`
