# Memory Integrity Audit

- generated_at: 2026-05-11T23:07:29.891403+00:00
- status_counts: {"ok":9,"warning":1}
- corrective_actions: none
- response_mode: recommendations only

## Checks

| Status | Check | Detail |
| --- | --- | --- |
| ok | dmn_schema | 59 records valid |
| ok | action_log_checksum_chain | checksum chain valid |
| ok | incident_index_links | missing_notes=none |
| ok | orphan_incident_notes | orphans=none |
| ok | duplicated_incident_ids | duplicates=none |
| ok | incident_references | missing_refs=none |
| ok | health_history_consistency | {"health_score":true,"path":true,"timestamp":true} |
| ok | baseline_report_matches_json | matched |
| ok | dashboard_values_match_source | matched |
| warning | daily_digest_values_match_source | dmn_append_count: digest=57 dashboard=58; dmn_append_count: digest=57 current=59 |

## Recommendations

- Regenerate derived dashboard or digest metadata when DMN counts need exact point-in-time alignment.
