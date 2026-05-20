# Runtime Hardening Report

## PatchRegistry

`restore_all()` now calls `clear_inactive()` after restoring handles — prevents inactive handle accumulation across wire/unwire cycles (v04 conftest pattern generalized).

## Replay boundary

- Default score path uses synthetic `AttentionForecast` — no replay file reads
- Identity `synthetic_containment_rate` remains bounded at 0.95 in forecaster evidence (unchanged)

**Runtime hardening:** PASS
