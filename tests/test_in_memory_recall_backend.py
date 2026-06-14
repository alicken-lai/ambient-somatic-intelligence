from __future__ import annotations

import inspect
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from memory.vector.base import RecallBackend, RecallFilter, RecallQueryContext
from memory.vector.in_memory_backend import BACKEND_NAME, InMemoryRecallBackend
import memory.vector.in_memory_backend as in_memory_backend


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _query_context() -> RecallQueryContext:
    return RecallQueryContext(
        recall_id="recall_in_memory_test",
        timestamp="2026-06-09T15:20:00+00:00",
        query_type="text",
        query_summary="wrapped memory proof harness query",
        query_hash="sha256:in-memory-test",
        initiating_agent="pytest",
        source_node="test-node",
        vector_backend=BACKEND_NAME,
        embedding_model="synthetic-in-memory",
        ranking_method="cosine_similarity_synthetic_embeddings",
        replay_reference={
            "available": True,
            "replay_id": "replay_in_memory_test",
            "source_path": "tests/test_in_memory_recall_backend.py",
            "timestamp": "2026-06-09T15:20:00+00:00",
            "reason": "",
        },
    )


def _sidecar(embedding: list[float], model: str = "synthetic-in-memory") -> dict:
    return {
        "embedding_model": model,
        "metadata": {
            "synthetic_embedding": embedding,
        },
    }


def _backend_with_records() -> InMemoryRecallBackend:
    backend = InMemoryRecallBackend()
    backend.add_record(
        _load_json("examples/wrapped_existing_memory/wrapped_dmn_record_001.example.json"),
        _sidecar([1.0, 0.0, 0.0]),
    )
    backend.add_record(
        _load_json("examples/wrapped_existing_memory/wrapped_dmn_record_002.example.json"),
        _sidecar([0.0, 1.0, 0.0]),
    )
    backend.add_record(
        _load_json("examples/wrapped_existing_memory/wrapped_dmn_record_003.example.json"),
        _sidecar([0.8, 0.2, 0.0]),
    )
    return backend


def test_backend_implements_interface() -> None:
    backend = InMemoryRecallBackend()
    assert isinstance(backend, RecallBackend)
    assert backend.backend_name == "in_memory_proof_harness"


def test_add_record_and_healthcheck() -> None:
    backend = InMemoryRecallBackend()
    record = _load_json("examples/wrapped_existing_memory/wrapped_dmn_record_001.example.json")
    backend.add_record(record, _sidecar([1.0, 0.0, 0.0]))
    health = backend.healthcheck()
    assert health["ok"] is True
    assert health["details"]["records"] == 1


def test_query_returns_ranked_candidates() -> None:
    backend = _backend_with_records()
    results = backend.query(
        [1.0, 0.0, 0.0],
        RecallFilter(tags=["wrapped-existing-memory"]),
        limit=3,
    )
    assert [result.rank for result in results] == [1, 2, 3]
    assert results[0].record_id == "mem_v1_dmn_line2_8f4f07e5d870"
    assert results[0].score >= results[1].score >= results[2].score


def test_filters_are_applied() -> None:
    backend = _backend_with_records()
    results = backend.query(
        [1.0, 0.0, 0.0],
        RecallFilter(
            privacy_class=["internal"],
            governance_state=["reviewed"],
            event_type=["governance_decision"],
            modality=["text"],
            tags=["Phase-1C"],
        ),
        limit=5,
    )
    assert [result.record_id for result in results] == [
        "mem_v1_dmn_line1502_a1a2b3ea07ea"
    ]
    assert results[0].privacy_filters_applied
    assert results[0].governance_filters_applied


def test_privacy_filters_fail_closed_if_unsupported() -> None:
    backend = InMemoryRecallBackend(support_privacy_filters=False)
    backend.add_record(
        _load_json("examples/wrapped_existing_memory/wrapped_dmn_record_001.example.json"),
        _sidecar([1.0, 0.0, 0.0]),
    )
    results = backend.query(
        [1.0, 0.0, 0.0],
        RecallFilter(privacy_class=["internal"]),
        limit=5,
    )
    assert results == []


def test_governance_filters_fail_closed_if_unsupported() -> None:
    backend = InMemoryRecallBackend(support_governance_filters=False)
    backend.add_record(
        _load_json("examples/wrapped_existing_memory/wrapped_dmn_record_001.example.json"),
        _sidecar([1.0, 0.0, 0.0]),
    )
    results = backend.query(
        [1.0, 0.0, 0.0],
        RecallFilter(governance_state=["raw"]),
        limit=5,
    )
    assert results == []


def test_tombstoned_records_are_not_returned() -> None:
    backend = _backend_with_records()
    backend.tombstone("mem_v1_dmn_line2_8f4f07e5d870", "contract test")
    results = backend.query(
        [1.0, 0.0, 0.0],
        RecallFilter(tags=["wrapped-existing-memory"]),
        limit=3,
    )
    assert "mem_v1_dmn_line2_8f4f07e5d870" not in [
        result.record_id for result in results
    ]


def test_exported_evidence_matches_schema_and_safety_defaults() -> None:
    backend = _backend_with_records()
    filters = RecallFilter(
        privacy_class=["internal"],
        governance_state=["raw", "reviewed"],
        tags=["wrapped-existing-memory"],
    )
    results = backend.query([1.0, 0.0, 0.0], filters, limit=2)
    evidence = backend.export_evidence(
        _query_context(),
        results,
        filters=filters,
        excluded_records=[
            {
                "record_id": "mem_v1_dmn_line3_4b34244df122",
                "reason": "privacy_class sensitive excluded by internal-only filter",
            }
        ],
    )

    assert evidence["guardian_visible"] is True
    assert evidence["decision_allowed"] is False
    assert evidence["action_allowed"] is False
    assert evidence["no_decision_made"] is True
    assert evidence["vector_backend"] == BACKEND_NAME
    assert evidence["candidate_record_ids"]

    schema = _load_json("schemas/recall_evidence.schema.json")
    Draft202012Validator(schema).validate(evidence)


def test_static_example_evidence_matches_schema() -> None:
    evidence = _load_json("examples/recall_evidence/in_memory_recall_evidence.example.json")
    schema = _load_json("schemas/recall_evidence.schema.json")
    Draft202012Validator(schema).validate(evidence)
    assert evidence["decision_allowed"] is False
    assert evidence["action_allowed"] is False


def test_no_turbovec_import_exists() -> None:
    source = inspect.getsource(in_memory_backend).casefold()
    assert "turbovec" not in source
    assert "turboquant" not in source
    assert "ryancodrai" not in source


def test_no_production_behavior_is_modified() -> None:
    caps = InMemoryRecallBackend().capabilities()
    assert caps["production_default"] is False
    assert caps["backend"] == BACKEND_NAME

