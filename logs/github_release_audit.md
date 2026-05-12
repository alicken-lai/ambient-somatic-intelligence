# GitHub Release Audit

- generated_at: 2026-05-12T09:35:00+00:00
- scope: first public GitHub push
- remote: `origin https://github.com/alicken-lai/ambient-somatic-intelligence.git`

## Status

- `git status`: clean except for the intended release-prep edits before commit
- `git remote`: origin configured for fetch and push

## Sensitive File Scan

No obvious secrets were found in the scanned text corpus:

- tokens
- API keys
- passwords
- OAuth caches
- `.env` files
- private keys
- browser cookies
- local machine credentials

## Public Surface

The following public-facing files were reviewed and are safe to publish as narrative/documentation:

- `README.md`
- `docs/public_architecture_snapshot.md`
- `docs/decision_boundary_protocol.md`
- `docs/release_readiness_audit.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

## Files That Should Remain Private

These files contain local paths, localhost URLs, container metadata, raw telemetry, or internal operational traces. They are useful for internal work, but they are not a clean public release surface:

- `tools/cua/screenshots/`
- `tools/cua/analysis/`
- `tools/cua/logs/`
- `observability/snapshots/`
- `logs/actions.jsonl`
- `logs/checksums.jsonl`
- `memory/dmn.jsonl`
- `guardian/approvals.jsonl`
- `guardian/incidents/`
- `guardian/health/`
- `guardian/simulations/`
- `guardian/dreams/`
- `guardian/recalibration/`
- `guardian/approval_packets/`

## Validation

- `python3 -m py_compile scripts/*.py`: passed
- `docker compose -f observability/docker-compose.yml config`: passed
- README structure: valid Markdown with a valid Mermaid block
- staged secret scan: no obvious secrets staged

## Recommendations

- Keep the root README, public architecture snapshot, decision boundary protocol, and release notes as the public narrative layer.
- Keep raw runtime artifacts under a separate private-only policy if the repository is later slimmed for external consumption.
- Re-run the secrets scan after any future CUA capture, incident write, or credential-related integration.
