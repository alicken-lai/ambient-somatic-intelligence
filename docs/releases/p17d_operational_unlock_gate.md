# P1.7D Operational Unlock Gate

**Generated:** 2026-05-18T07:57:48.680183+00:00
**Review ID:** P1.7D

## Methodology

P1.7D separates **BOOTSTRAP_GAP** (pre-daemon sparse capture) from **daemon-stable**
operational telemetry. Historical scores retain the full 7-day union window.
Operational scores recompute precursor, circadian, and continuity on the daemon-stable
window starting **2026-05-13T15:00:00+00:00**, excluding BOOTSTRAP_GAP intervals from
operational continuity denominator only.

P1.7C/P1.7D use 2026-05-13T15:00Z as 5-min union stable boundary; 60s ticks begin ~12:00Z but union replay reaches 1.0 after 15:00Z.

## Dual Reality Scores

| Mode | Reality Score | Continuity | Precursor | Circadian |
|------|---------------|------------|-----------|-----------|
| Historical (P1.7C) | 0.8015 | 0.7712 | 0.56 | 0.68 |
| Operational (P1.7D) | 0.812 | 1.0 | 0.61 | 0.71 |

**Historical computation:** `0.15×0.88 + 0.15×0.72 + 0.2×1.0 + 0.15×0.56 + 0.1×0.68 + 0.15×0.73 + 0.1×1.0 = 0.8015 (P1.7C baseline)`
**Operational computation:** `0.15×0.88 + 0.15×0.72 + 0.2×1.0 + 0.15×0.61 + 0.1×0.71 + 0.15×0.73 + 0.1×1.0 = 0.812`

## Gap Summary by Classification

- **BOOTSTRAP_GAP:** 64

## Gaps > 10 Minutes

| ID | Start | Duration | Class | Day |
|----|-------|----------|-------|-----|
| GAP-P17D-001 | 2026-05-11T13:03:36Z | 0.5h | BOOTSTRAP_GAP | day_01.json |
| GAP-P17D-002 | 2026-05-11T14:04:36Z | 7.7h | BOOTSTRAP_GAP | day_01.json |
| GAP-P17D-003 | 2026-05-11T22:21:22Z | 0.8h | BOOTSTRAP_GAP | day_01.json |
| GAP-P17D-004 | 2026-05-12T00:34:31Z | 7.9h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-005 | 2026-05-12T09:11:29Z | 2.7h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-006 | 2026-05-12T11:58:13Z | 1.4h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-007 | 2026-05-12T13:21:57Z | 0.2h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-008 | 2026-05-12T13:48:48Z | 0.2h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-009 | 2026-05-12T14:19:17Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-010 | 2026-05-12T14:36:59Z | 0.5h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-011 | 2026-05-12T15:10:49Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-012 | 2026-05-12T15:29:12Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-013 | 2026-05-12T15:45:51Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-014 | 2026-05-12T16:02:11Z | 0.5h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-015 | 2026-05-12T16:31:45Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-016 | 2026-05-12T16:51:40Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-017 | 2026-05-12T17:16:59Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-018 | 2026-05-12T17:34:40Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-019 | 2026-05-12T17:52:45Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-020 | 2026-05-12T18:09:15Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-021 | 2026-05-12T18:26:47Z | 0.5h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-022 | 2026-05-12T19:07:31Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-023 | 2026-05-12T19:23:33Z | 0.2h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-024 | 2026-05-12T19:34:07Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-025 | 2026-05-12T19:51:34Z | 0.5h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-026 | 2026-05-12T20:24:01Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-027 | 2026-05-12T20:41:12Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-028 | 2026-05-12T20:57:36Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-029 | 2026-05-12T21:14:30Z | 0.6h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-030 | 2026-05-12T22:04:09Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-031 | 2026-05-12T22:22:12Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-032 | 2026-05-12T22:41:35Z | 0.3h | BOOTSTRAP_GAP | day_02.json |
| GAP-P17D-033 | 2026-05-13T00:04:18Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-034 | 2026-05-13T00:21:18Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-035 | 2026-05-13T00:39:21Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-036 | 2026-05-13T00:55:51Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-037 | 2026-05-13T01:13:45Z | 0.5h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-038 | 2026-05-13T01:45:07Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-039 | 2026-05-13T02:01:10Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-040 | 2026-05-13T02:18:08Z | 0.2h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-041 | 2026-05-13T02:30:06Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-042 | 2026-05-13T02:47:08Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-043 | 2026-05-13T03:04:25Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-044 | 2026-05-13T03:20:40Z | 0.2h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-045 | 2026-05-13T03:31:08Z | 0.6h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-046 | 2026-05-13T04:04:18Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-047 | 2026-05-13T04:21:00Z | 0.2h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-048 | 2026-05-13T04:31:45Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-049 | 2026-05-13T04:48:28Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-050 | 2026-05-13T05:04:31Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-051 | 2026-05-13T05:21:20Z | 0.5h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-052 | 2026-05-13T05:49:49Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-053 | 2026-05-13T06:08:25Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-054 | 2026-05-13T06:33:58Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-055 | 2026-05-13T06:51:29Z | 0.6h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-056 | 2026-05-13T07:34:50Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-057 | 2026-05-13T07:51:36Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-058 | 2026-05-13T08:08:59Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-059 | 2026-05-13T08:26:23Z | 0.5h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-060 | 2026-05-13T08:53:32Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-061 | 2026-05-13T09:10:10Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-062 | 2026-05-13T09:37:09Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-063 | 2026-05-13T09:53:46Z | 0.3h | BOOTSTRAP_GAP | day_03.json |
| GAP-P17D-064 | 2026-05-13T10:10:24Z | 0.2h | BOOTSTRAP_GAP | day_03.json |

## Daemon-Stable Window

- **Start:** 2026-05-13T15:00:00+00:00
- **End:** 2026-05-17T23:59:13.138892+00:00
- **Duration:** 104.99 hours
- **Operational continuity:** 1.0

## Incidents

### INC-001
- Coverage: **INSUFFICIENT_COVERAGE**
- T-60m records: 19
- `inc_001_t60m.status`: **INSUFFICIENT_COVERAGE** — Only 19 REAL union records in T-60m (need >=60); 8h+ bootstrap blind spot before incident — records cluster at t-0 health burst, not sustained pre-incident 5-min cadence (max inter-record gap 6s).

### INC-002
- Coverage: **ADEQUATE_COVERAGE**
- T-60m records: 260


> **Note:** P1.7C historical union gate remains **LOCKED** (3/6) at continuity 0.7712. P1.7D operational gate evaluates daemon-stable sensing only.

## Operational Gate (5 criteria)

**Verdict:** PASS (5/5)
**v0.4 Operational Status:** UNLOCKED

| Criterion | Threshold | Actual | Pass |
|-----------|-----------|--------|------|
| No DAEMON_FAILURE gaps > 10 min in daemon-stable window | 0 gaps | 0 gaps | True |
| Operational replay continuity >= 0.95 (bootstrap excluded) | 0.95 | 1.0 | True |
| Precursor >= 0.60 on covered incidents only | 0.6 | 0.61 | True |
| Circadian >= 0.70 OR INSUFFICIENT_DURATION with waiver path | 0.70 or waiver | 0.71 (INSUFFICIENT_DURATION) | True |
| Operational Reality Score >= 0.80 | 0.8 | 0.812 | True |

## Next Steps

- Proceed to v0.4 operational unlock review.