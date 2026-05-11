# Night 1 Substrate Hardening

Timestamp: 2026-05-11T13:00:54Z

## Dependency State

- `uv`: uv 0.11.13 (Homebrew 2026-05-11 aarch64-apple-darwin)
- `node`: v26.0.0
- `npm`: 11.12.1
- `docker`: Docker version 29.4.3, build 055a478ea9
- Docker daemon: not running at `unix:///var/run/docker.sock`

## Hardening Added

- Structured action logging in `logs/actions.jsonl`
- Guardian approval records in `guardian/approvals.jsonl`
- DMN schema file in `memory/schema.json`
- DMN validation command through `scripts/remember.py validate`
- Immutable checksum chain in `logs/checksums.jsonl`
- File lock for checksum writes at `logs/.checksum.lock`
- Minimal Guardian-gated action router in `scripts/action_router.py`

## Verification

- Python syntax check passed with local bytecode cache.
- Guardian classified `brew install uv node docker` as `REVIEW_REQUIRED` and recorded approval.
- DMN memory validation passed for 1 record.
- Router executed `uptime` through Guardian with `ALLOW`.
- Checksum chain recorded `logs/night0.log`.
- Checksum writer locking added after concurrent smoke tests exposed a pre-commit chain race.
- Pre-commit checksum records were relinked in file order and the repair was logged.

## Deferred

- CUA: scaffold only
- Prometheus/Grafana: scaffold only
- PrintingPress: scaffold only
- MemPalace: scaffold only
