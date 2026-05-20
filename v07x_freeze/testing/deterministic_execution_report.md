# Deterministic Execution Report

**Audit date:** 2026-05-20

## Pytest stability

- Full v060–v077 stack: **395 passed**, 0 failed, 0 flaky on single run
- No `pytest.mark.flaky` in v07x tests
- v072/v073/v075/v076/v077 use `conftest.py` for isolated fixtures (no shared mutable globals observed)

## PatchRegistry

- v07x tests do **not** register kernel patches
- `PatchRegistry` teardown patterns exist in `tests/v04/conftest.py` only — no contamination in civilization regression path

## Score + pytest independence

Observability scores do not depend on pytest execution order or prior test state.

**Deterministic execution: PASS**
