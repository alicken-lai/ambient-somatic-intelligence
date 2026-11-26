"""P5 adversarial tests. All writes are restricted to pytest temporary roots."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from hermes.audit.institutional_health import INSTITUTIONAL_WEIGHTS, generate_audit_report
from hermes.evidence_snapshot import (
    ReadOnlyEvidenceSnapshot, SnapshotMutationError, canonical_json_bytes,
    content_addressed_document, export_metric_evidence, load_metric_evidence,
    metric_reference, metric_references, observation_reference, sha256_bytes,
    verify_content_addressed_document, write_bytes_if_changed,
)
from hermes.graph.persistent_graph import (
    GRAPH_PATH, GRAPH_SOURCES, compute_persistent_graph_health, export_persistent_graph,
)
from hermes.release.rc_health import RC_METRICS, compute_rc_health, generate_release_report
from tools.check_rc1_readiness import _coerce_float, check_health_thresholds, check_release_ready_flag
from tools.validate_dmn_events import normalize_record, validate_dmn, validate_dmn_bytes

NOW = datetime(2026, 9, 16, 12, tzinfo=timezone.utc)
MAX_AGE = 3600
OPTIONS = {"now": NOW, "max_age_seconds": MAX_AGE}
ROOT = Path(__file__).resolve().parents[1]


def put(root, ref, value):
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else canonical_json_bytes(value))
    os.utime(path, (NOW.timestamp() - 10, NOW.timestamp() - 10))
    return path


def age(path, seconds):
    stamp = NOW.timestamp() - seconds
    os.utime(path, (stamp, stamp))


def metric(root, name, outcomes=("PASS", "PASS")):
    put(root, observation_reference(name), {
        "schema": "asi-metric-observations/v1", "metric": name,
        "producer": "isolated-test-fixture-not-release-evidence",
        "measured_at": (NOW - timedelta(seconds=10)).isoformat(),
        "checks": [{"id": str(i), "outcome": outcome} for i, outcome in enumerate(outcomes)],
    })
    document = export_metric_evidence(root, name, **OPTIONS)
    age(root / metric_reference(name), 10)
    return document


def graph_sources(root):
    put(root, GRAPH_SOURCES[0], {"s1": {"skill_id": "s1", "task_types": ["architecture", "debugging"]}})
    put(root, GRAPH_SOURCES[1], {"t1": {"trust_id": "t1", "entity_id": "s1",
                                       "last_updated": (NOW - timedelta(seconds=20)).isoformat()}})
    put(root, GRAPH_SOURCES[2], {"identity_id": "asi", "core_values": ["safety"],
                               "core_principles": ["evidence"], "long_term_objectives": ["continuity"],
                               "last_updated": (NOW - timedelta(seconds=20)).isoformat()})
    export_persistent_graph(root, **OPTIONS)
    age(root / GRAPH_PATH, 10)


@pytest.fixture
def ready_root(tmp_path):
    for name in (*RC_METRICS, *INSTITUTIONAL_WEIGHTS):
        metric(tmp_path, name)
    graph_sources(tmp_path)
    put(tmp_path, "schemas/dmn_event.schema.json", (ROOT / "schemas/dmn_event.schema.json").read_bytes())
    put(tmp_path, "memory/dmn.jsonl", canonical_json_bytes({
        "event_type": "EVIDENCE_EVENT", "content": "isolated fixture", "timestamp": NOW.isoformat(),
    }))
    return tmp_path


def test_measured_release_uses_actual_counts(ready_root):
    metric(ready_root, "test_health", ("PASS", "FAIL", "ERROR", "SKIP"))
    result = compute_rc_health(ready_root, **OPTIONS)
    assert result["components"]["test_health"] == 25
    assert result["rc_health"] == 86.5
    assert result["release_ready"] is True  # original weighted thresholds retained
    assert verify_content_addressed_document(result)
    metric(ready_root, "test_health", ("FAIL",))
    result = compute_rc_health(ready_root, **OPTIONS)
    assert result["rc_health"] == 82
    assert result["release_ready"] is False


@pytest.mark.parametrize("name", [*RC_METRICS, *INSTITUTIONAL_WEIGHTS])
@pytest.mark.parametrize("fault", ["missing", "stale", "future", "bad_hash", "invalid_json"])
def test_each_metric_fault_blocks_release(ready_root, name, fault):
    path = ready_root / metric_reference(name)
    if fault == "missing":
        path.rename(path.with_suffix(".unavailable"))
    elif fault in ("stale", "future"):
        age(path, MAX_AGE + 1 if fault == "stale" else -1)
    elif fault == "bad_hash":
        raw = json.loads(path.read_bytes())
        raw["content_sha256"] = "0" * 64
        put(ready_root, metric_reference(name), raw)
    else:
        put(ready_root, metric_reference(name), b"not JSON")
    result = compute_rc_health(ready_root, **OPTIONS)
    assert result["status"] == "UNKNOWN"
    assert result["rc_health"] is None
    assert result["release_ready"] is False


@pytest.mark.parametrize("score", [True, None, "100", -1, 101, [], {}, float("nan"), float("inf"), -float("inf")])
def test_invalid_metric_numbers(ready_root, score):
    name = "test_health"
    path = ready_root / metric_reference(name)
    raw = json.loads(path.read_bytes())
    raw["score"] = score
    if isinstance(score, float) and not (-float("inf") < score < float("inf")):
        put(ready_root, metric_reference(name), json.dumps(raw).encode())
    else:
        put(ready_root, metric_reference(name), content_addressed_document(raw))
    result = compute_rc_health(ready_root, **OPTIONS)
    assert result["components"][name] is None
    assert result["release_ready"] is False


@pytest.mark.parametrize("fault", ["missing", "stale", "future", "measurement_stale", "measurement_future",
                                   "no_timezone", "empty", "duplicate", "invalid_outcome", "source_change"])
def test_raw_observation_validation(ready_root, fault):
    name = "test_health"
    ref = observation_reference(name)
    path = ready_root / ref
    raw = json.loads(path.read_bytes())
    if fault == "missing":
        path.rename(path.with_suffix(".unavailable"))
    elif fault in ("stale", "future"):
        age(path, MAX_AGE + 1 if fault == "stale" else -1)
    else:
        if fault == "measurement_stale":
            raw["measured_at"] = (NOW - timedelta(hours=2)).isoformat()
        elif fault == "measurement_future":
            raw["measured_at"] = (NOW + timedelta(seconds=1)).isoformat()
        elif fault == "no_timezone":
            raw["measured_at"] = "2026-09-16T11:59:50"
        elif fault == "empty":
            raw["checks"] = []
        elif fault == "duplicate":
            raw["checks"][1]["id"] = raw["checks"][0]["id"]
        elif fault == "invalid_outcome":
            raw["checks"][0]["outcome"] = "SUCCESS"
        else:
            raw["checks"][0]["outcome"] = "FAIL"
        put(ready_root, ref, raw)
    assert compute_rc_health(ready_root, **OPTIONS)["release_ready"] is False


def test_rehashed_fabricated_score_is_rejected(ready_root):
    name = "test_health"
    metric(ready_root, name, ("PASS", "FAIL"))
    raw = json.loads((ready_root / metric_reference(name)).read_bytes())
    raw["score"] = 100
    put(ready_root, metric_reference(name), content_addressed_document(raw))
    snap = ReadOnlyEvidenceSnapshot.capture(ready_root, metric_references([name]), **OPTIONS)
    assert load_metric_evidence(snap, metric_reference(name), metric=name)["reason"] == "measurement_mismatch"


@pytest.mark.parametrize("ref", [GRAPH_PATH, *GRAPH_SOURCES])
@pytest.mark.parametrize("fault", ["missing", "stale", "future", "invalid"])
def test_graph_authority_fault_blocks_release(ready_root, ref, fault):
    path = ready_root / ref
    if fault == "missing":
        path.rename(path.with_suffix(".unavailable"))
    elif fault in ("stale", "future"):
        age(path, MAX_AGE + 1 if fault == "stale" else -1)
    else:
        put(ready_root, ref, {"bad": "shape"})
    assert compute_rc_health(ready_root, **OPTIONS)["release_ready"] is False


def test_graph_is_deterministic_and_uses_real_source_content(ready_root):
    before = (ready_root / GRAPH_PATH).read_bytes()
    output_mtime = (ready_root / GRAPH_PATH).stat().st_mtime_ns
    source_metadata = {ref: ((ready_root / ref).read_bytes(), (ready_root / ref).stat().st_mtime_ns) for ref in GRAPH_SOURCES}
    for _ in range(2):
        document = export_persistent_graph(ready_root, **OPTIONS)
        assert (ready_root / GRAPH_PATH).read_bytes() == before
        assert (ready_root / GRAPH_PATH).stat().st_mtime_ns == output_mtime
    assert {ref: ((ready_root / ref).read_bytes(), (ready_root / ref).stat().st_mtime_ns) for ref in GRAPH_SOURCES} == source_metadata
    assert {"source": "architecture", "relation": "uses_skill", "target": "s1"} in document["edges"]
    put(ready_root, GRAPH_SOURCES[0], {"s2": {"skill_id": "s2", "task_types": ["new-task"]}})
    assert compute_rc_health(ready_root, **OPTIONS)["release_ready"] is False
    new = export_persistent_graph(ready_root, **OPTIONS)
    assert new["content_sha256"] != document["content_sha256"]
    assert {"source": "new-task", "relation": "uses_skill", "target": "s2"} in new["edges"]
    assert new["sources"][0]["sha256"] == sha256_bytes((ready_root / GRAPH_SOURCES[0]).read_bytes())


def test_rehashed_graph_tampering_rejected(ready_root):
    raw = json.loads((ready_root / GRAPH_PATH).read_bytes())
    raw["edges"][0]["target"] = "fabricated"
    put(ready_root, GRAPH_PATH, content_addressed_document(raw))
    result = compute_persistent_graph_health(ready_root, **OPTIONS)
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "graph_source_or_content_mismatch"


@pytest.mark.parametrize("offset", [-7200, 1])
def test_graph_internal_observation_cannot_be_refreshed_by_touch(ready_root, offset):
    raw = json.loads((ready_root / GRAPH_SOURCES[1]).read_bytes())
    raw["t1"]["last_updated"] = (NOW + timedelta(seconds=offset)).isoformat()
    put(ready_root, GRAPH_SOURCES[1], raw)
    with pytest.raises(ValueError, match="not fresh"):
        export_persistent_graph(ready_root, **OPTIONS)
    assert compute_rc_health(ready_root, **OPTIONS)["release_ready"] is False


def test_snapshots_capture_immutable_bytes_and_detect_content_or_mtime_mutation(tmp_path):
    path = put(tmp_path, "x.json", {"x": 1})
    snapshot = ReadOnlyEvidenceSnapshot.capture(tmp_path, ["x.json"], **OPTIONS)
    age(path, 20)
    with pytest.raises(SnapshotMutationError):
        snapshot.assert_unchanged()
    put(tmp_path, "x.json", {"x": 2})
    assert snapshot.read_json("x.json") == {"x": 1}
    with pytest.raises(SnapshotMutationError):
        snapshot.assert_unchanged()


def test_snapshot_missing_then_created_is_mutation(tmp_path):
    snapshot = ReadOnlyEvidenceSnapshot.capture(tmp_path, ["x"], **OPTIONS)
    put(tmp_path, "x", b"created")
    with pytest.raises(SnapshotMutationError):
        snapshot.assert_unchanged()


@pytest.mark.parametrize("ref", ["../x", "/x", "C:/outside", "C:relative", "\\\\host\\share", ""])
def test_snapshot_rejects_unsafe_references(tmp_path, ref):
    with pytest.raises(ValueError):
        ReadOnlyEvidenceSnapshot.capture(tmp_path, [ref], **OPTIONS)


@pytest.mark.parametrize("max_age", [-1, float("nan"), float("inf"), True])
def test_snapshot_invalid_freshness_policy(tmp_path, max_age):
    with pytest.raises(ValueError):
        ReadOnlyEvidenceSnapshot.capture(tmp_path, [], now=NOW, max_age_seconds=max_age)


def tree_state(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


def test_readonly_and_report_noop_purity(ready_root, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("lower-layer exporter invoked")
    monkeypatch.setattr("hermes.graph.persistent_graph.export_persistent_graph", forbidden)
    monkeypatch.setattr("hermes.evidence_snapshot.export_metric_evidence", forbidden)
    monkeypatch.setattr("hermes.graph.graph_health.build_audit_graph", forbidden)
    before = tree_state(ready_root)
    first = compute_rc_health(ready_root, **OPTIONS)
    second = compute_rc_health(ready_root, now=NOW + timedelta(seconds=1), max_age_seconds=MAX_AGE)
    assert first == second
    assert before == tree_state(ready_root)
    report = ready_root / "output/release.md"
    audit = ready_root / "output/audit.md"
    generate_release_report(report, root=ready_root, **OPTIONS)
    generate_audit_report(audit, root=ready_root, **OPTIONS)
    generated = tree_state(ready_root)
    generate_release_report(report, root=ready_root, now=NOW + timedelta(seconds=2), max_age_seconds=MAX_AGE)
    generate_audit_report(audit, root=ready_root, now=NOW + timedelta(seconds=2), max_age_seconds=MAX_AGE)
    assert generated == tree_state(ready_root)
    for ref, value in before.items():
        assert generated[ref] == value


def test_metric_writer_noop(tmp_path):
    metric(tmp_path, "test_health")
    path = tmp_path / metric_reference("test_health")
    stamp = path.stat().st_mtime_ns
    export_metric_evidence(tmp_path, "test_health", **OPTIONS)
    assert path.stat().st_mtime_ns == stamp
    assert write_bytes_if_changed(path, path.read_bytes()) is False


def test_mutation_during_release_is_unknown(ready_root, monkeypatch):
    import hermes.release.rc_health as module
    original = module.load_graph_authority
    def mutate(snapshot):
        result = original(snapshot)
        age(ready_root / GRAPH_SOURCES[0], 20)
        return result
    monkeypatch.setattr(module, "load_graph_authority", mutate)
    result = compute_rc_health(ready_root, **OPTIONS)
    assert result["status"] == "UNKNOWN"
    assert result["release_ready"] is False
    assert "snapshot" in result["component_status"]


def test_unknown_event_and_legacy_lineage_never_rewrite(tmp_path):
    records = [
        {"content": "Unclassified historical note", "timestamp": "then"},
        {"content": "Guardian allowed audit", "timestamp": "then"},
        {"event_type": "UNKNOWN_EVENT", "content": "unknown", "timestamp": "then"},
        {"event_type": "FAILURE_EVENT", "content": "FAIL retained", "timestamp": "then"},
        {"event_type": None, "content": "invalid explicit type", "timestamp": "then"},
    ]
    raw = b"".join(canonical_json_bytes(r).replace(b"\n", b"\r\n") for r in records) + b"broken\r\n"
    path = put(tmp_path, "dmn.jsonl", raw)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    result = validate_dmn(path, ROOT / "schemas/dmn_event.schema.json")
    assert result["legacy_inferred"] == 2
    assert result["unknown_events"] == 2
    assert result["explicit_events"] == 3
    assert result["invalid"] == 2
    assert result["status"] == "UNKNOWN"
    assert result["legacy_inference_types"] == {"GUARDIAN_EVENT": 1, "UNKNOWN_EVENT": 1}
    assert result["source_sha256"] == sha256_bytes(raw)
    assert result["lineage"][0]["sha256"] == sha256_bytes(raw.splitlines(keepends=True)[0])
    assert before == (path.read_bytes(), path.stat().st_mtime_ns)
    assert normalize_record(records[0])["event_type"] == "UNKNOWN_EVENT"


@pytest.mark.parametrize("raw", [b"", b"\n", b"null\n", b"[]\n", b"broken\n",
                                    b'{"event_type": [], "content": "x", "timestamp": "t"}\n'])
def test_invalid_or_empty_dmn_is_unknown(raw):
    result = validate_dmn_bytes(raw, (ROOT / "schemas/dmn_event.schema.json").read_bytes())
    assert result["status"] == "UNKNOWN"


def test_unknown_and_inferred_events_block_ready_root(ready_root):
    for event in ({"event_type": "UNKNOWN_EVENT"}, {}, {"event_type": None}):
        put(ready_root, "memory/dmn.jsonl", canonical_json_bytes({
            **event, "content": "Guardian legacy note", "timestamp": NOW.isoformat(),
        }))
        result = compute_rc_health(ready_root, **OPTIONS)
        assert result["components"]["dmn_health"] is None
        assert result["release_ready"] is False


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, "100", 101, -1, None])
def test_readiness_checker_rejects_invalid_numbers(value):
    assert _coerce_float(value) is None


def test_readiness_checker_does_not_trust_legacy_pass(tmp_path):
    put(tmp_path, "reports/v09_release_report.json", {
        "rc_health": 100, "release_ready": True,
        "components": {"graph_health": 100, "dmn_health": 100},
    })
    assert check_health_thresholds(tmp_path)[1]
    assert check_release_ready_flag(tmp_path)


def test_readiness_checker_rechecks_current_evidence(ready_root, monkeypatch):
    import tools.check_rc1_readiness as checker
    monkeypatch.setattr(checker, "compute_rc_health", lambda base: compute_rc_health(base, **OPTIONS))
    generate_release_report(ready_root / "reports/v09_release_report.md", root=ready_root, **OPTIONS)
    assert check_health_thresholds(ready_root)[1] == []
    assert check_release_ready_flag(ready_root) == []
    age(ready_root / GRAPH_PATH, MAX_AGE + 1)
    assert check_health_thresholds(ready_root)[1]
    assert check_release_ready_flag(ready_root)


@pytest.mark.parametrize("target", ["dmn", "schema"])
def test_dmn_cli_cannot_overwrite_its_inputs(tmp_path, target):
    from tools.validate_dmn_events import main
    dmn = put(tmp_path, "dmn.jsonl", b'{"content":"historical failure"}\n')
    schema = put(tmp_path, "schema.json", (ROOT / "schemas/dmn_event.schema.json").read_bytes())
    before = tree_state(tmp_path)
    with pytest.raises(ValueError, match="aliases evidence"):
        main(["--dmn", str(dmn), "--schema", str(schema),
              "--output", str(dmn if target == "dmn" else schema)])
    assert tree_state(tmp_path) == before


def test_validation_harness_fails_when_sources_change():
    import importlib.util
    spec = importlib.util.spec_from_file_location("p5_harness", ROOT / "tests/p5_run_validation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validation_exit_code(0, {"source": "old"}, {"source": "new"}) == 1
    assert module.validation_exit_code(0, {"source": "old"}, {"source": "old"}) == 0
    assert module.validation_exit_code(2, {"source": "old"}, {"source": "old"}) == 2
