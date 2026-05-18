# P1.7C Reality Gate

**Generated:** 2026-05-18T07:53:04.194353+00:00
**Verdict:** FAIL (3/6)
**v0.4 Status:** LOCKED

## Reality Score: 0.8015

```
0.15×0.88 + 0.15×0.72 + 0.2×1.0 + 0.15×0.56 + 0.1×0.68 + 0.15×0.73 + 0.1×1.0 = 0.8015
```

| # | Criterion | Threshold | Actual | Verdict |
|---|-----------|-----------|--------|---------|
| 1 | 7 full days of REAL telemetry captured | 7/7 | 7/7 | PASS |
| 2 | No interpolated records in scoring | 0 used | 121 excluded (audit) | PASS |
| 3 | Reality Score >= 0.80 | 0.8 | 0.8015 | PASS |
| 4 | Precursor detection >= 0.60 | 0.6 | 0.56 | FAIL |
| 5 | Circadian adaptation >= 0.70 | 0.7 | 0.68 | FAIL |
| 6 | Replay continuity >= 0.95 | 0.95 | 0.7712 | FAIL |

## 7-Day Capture

| Day | Date | Status | Records | Max Gap |
|-----|------|--------|---------|---------|
| day_01 | 2026-05-11 | PARTIAL | 664 | 27857.24 |
| day_02 | 2026-05-12 | CAPTURED | 1420 | 28463.27 |
| day_03 | 2026-05-13 | CAPTURED | 8536 | 2062.51 |
| day_04 | 2026-05-14 | CAPTURED | 14500 | 240.1 |
| day_05 | 2026-05-15 | CAPTURED | 14390 | 64.13 |
| day_06 | 2026-05-16 | CAPTURED | 14380 | 64.0 |
| day_07 | 2026-05-17 | CAPTURED | 14380 | 63.32 |

## Replay Continuity: 0.7712

Union-window 5-minute slot occupancy over materialized day_01–day_07 REAL records. occupied_slots/expected_slots; slot=300s. Daemon-era (>=2026-05-13T15:00Z) continuity=1.0000.

## Next Recommendation

Continue daemon-era capture through 2026-05-18 EOD to lift circadian data_sufficiency; backfill day_01–02 sparse windows (28k+ s gaps) to raise union replay continuity above 0.95; enrich INC-001 precursor windows (only 19 REAL records at t−60m) via sustained pre-incident sampling. Re-run p17c_materialize after fixes. Blockers: Precursor detection >= 0.60, Circadian adaptation >= 0.70, Replay continuity >= 0.95.