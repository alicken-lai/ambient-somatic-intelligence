# Historical DMN Replay Coverage Report

Phase: 1G.9
Status: Read-only audit.

## Replay Coverage

| Replay Coverage Status | Count | Percentage |
| --- | --- | --- |
| derived | 2 | 4.0% |
| missing | 11 | 22.0% |
| unknown | 37 | 74.0% |

## Impact On Auditability

Source line and hash allow derived provenance, but missing explicit replay pointers limit full reconstruction. Records without replay manifests should not become automatic sync or vector-recall candidates.

## Recommendation

Create replay sidecar proposals that link historical DMN source lines to manifests, causal event IDs, and root event IDs where evidence exists.
