# Release Readiness Audit

- generated_at: 2026-05-12T09:18:00+00:00
- scope: public release safety review
- corrective_actions: none
- response_mode: recommendations only

## Summary

The public-facing narrative files are in acceptable shape for release, and no obvious secrets, API keys, bearer tokens, or private credentials were found in the inspected text files.

The main release risk is not credential leakage. It is the presence of raw runtime artifacts that embed local paths, localhost URLs, Docker metadata, and host-specific observation output.

## Checks

| Check | Result | Detail |
| --- | --- | --- |
| secrets_scan | ok | no obvious API keys, private keys, bearer tokens, or passwords detected in the inspected text corpus |
| README_public_safe | ok | `README.md` avoids local paths, tokens, and machine identifiers |
| docs_public_safe | ok | public architecture and protocol docs remain descriptive and non-secret |
| dashboard_public_safe | ok | `dashboard/daily_digest.md` is summary-only and does not expose credentials |
| runtime_artifacts_private | warn | screenshots, analysis JSON, telemetry snapshots, and raw logs still contain host-specific paths and environment data |
| ignore_rules_updated | ok | `.gitignore` now excludes transient screenshot, analysis, log, and snapshot directories |

## Private Artifacts To Keep Out Of A Public Release

- `tools/cua/screenshots/`
- `tools/cua/analysis/`
- `tools/cua/logs/`
- `observability/snapshots/`
- `logs/actions.jsonl`
- `logs/checksums.jsonl`
- `memory/dmn.jsonl`
- `guardian/approvals.jsonl`
- `guardian/incidents/*.md` and `guardian/incidents/index.json`
- `guardian/health/*.json`
- `guardian/simulations/*.json`
- `guardian/dreams/*.json`
- `guardian/recalibration/*.json`
- `guardian/approval_packets/*.json`

These files are useful for internal auditability, but they are not a clean public surface because they can expose `/Users/...`, `localhost`, container metadata, and raw operational traces.

## Recommendations

- Publish the README, architecture snapshot, and boundary docs as the public surface.
- Keep the raw runtime corpus out of the public release bundle.
- If the full repository must be published, generate a scrubbed export or separate public branch instead of shipping the working tree unchanged.
- Re-run the release audit whenever new CUA captures, incident payloads, or telemetry snapshots are generated.
