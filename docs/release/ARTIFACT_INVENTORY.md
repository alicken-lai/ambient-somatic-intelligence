# v0.9 Release Artifact Inventory

## Source Code

- `hermes/deliberation/`
- `hermes/verification/`
- `hermes/acquisition/`
- `hermes/calibration/`
- `hermes/reality_alignment/`
- `hermes/identity/`
- `hermes/audit/`
- `hermes/graph/`
- `hermes/release/`
- `scripts/hermes.py`

## Schemas

- `schemas/dmn_event.schema.json`
- `schemas/memory_event.schema.json`
- `schemas/recall_evidence.schema.json`
- `schemas/governed_memory_wrapper.schema.json`
- `schemas/dmn_metadata_sidecar.schema.json`

## Reports

- `reports/institutional_audit_report.md/json`
- `reports/graph_health_report.md/json`
- `reports/v09_release_report.md/json`
- Phase 1-9 generated evidence reports under `reports/`

## Documentation

- `README.md`
- `docs/architecture/HERMES_ASI_V09.md`
- `docs/audit/`
- `docs/release/`
- `docs/DMN_EVENT_TAXONOMY.md`

## Tests

- `tests/test_institutional_audit.py`
- `tests/test_dmn_taxonomy.py`
- `tests/test_graph_health.py`
- `tests/test_release_health.py`
- `tests/test_report_determinism.py`
- Phase 1-9 focused tests

## Runtime Artifacts

- `logs/`
- `state/`
- `memory/dmn.jsonl`
- `logs/dmn_reflection_cycle/`

## Ignored / Should Remain Local

- `.codex_*_prompt.txt`
- `_run.txt`
- `_v*_run.txt`
- daemon locks
- raw stdout/stderr logs
