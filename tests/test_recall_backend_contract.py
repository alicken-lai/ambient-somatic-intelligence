from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from memory.vector import base
from memory.vector.base import (
    RecallBackend,
    RecallFilter,
    RecallProvenance,
    RecallQueryContext,
    RecallResult,
    failure_evidence,
)


class FakeRecallBackend(RecallBackend):
    backend_name = "fake_contract_backend"

    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.tombstones: dict[str, str] = {}

    def add_record(
        self,
        record: dict[str, Any],
        embedding_sidecar: dict[str, Any] | None = None,
    ) -> None:
        self.records[record["record_id"]] = {
            "record": record,
            "embedding_sidecar": embedding_sidecar,
        }

    def query(
        self,
        query_embedding: list[float] | None,
        filters: RecallFilter,
        limit: int,
    ) -> list[RecallResult]:
        if not self.records or limit <= 0:
            return []
        record_id = next(iter(self.records))
        if record_id in self.tombstones:
            return []
        return [
            RecallResult(
                record_id=record_id,
                score=0.75,
                rank=1,
                backend=self.backend_name,
                embedding_model="none",
                provenance=RecallProvenance(
                    source_path="examples/wrapped_existing_memory/wrapped_dmn_record_001.example.json",
                    source_line=1,
                    content_hash="sha256:test",
                    backend=self.backend_name,
                ),
                filters_applied=filters.applied(),
                privacy_filters_applied=["privacy_class=['internal']"],
                governance_filters_applied=["governance_state=['raw']"],
                replay_pointer={
                    "available": True,
                    "replay_id": "replay_fake_contract",
                },
            )
        ]

    def tombstone(self, record_id: str, reason: str) -> dict[str, Any]:
        self.tombstones[record_id] = reason
        return {"record_id": record_id, "reason": reason, "tombstoned": True}

    def healthcheck(self) -> dict[str, Any]:
        return {
            "ok": True,
            "backend": self.backend_name,
            "status": "contract-test-only",
            "details": {},
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "supported_filters": [
                "privacy_class",
                "governance_state",
                "source_node",
                "event_type",
                "modality",
                "retention_policy",
                "time_range",
                "tags",
            ],
            "unsupported_filters": [],
            "requires_embeddings": False,
            "supports_tombstones": True,
            "supports_evidence_export": True,
            "failure_behavior": "empty_candidate_set_with_failure_evidence",
        }


def _query_context() -> RecallQueryContext:
    return RecallQueryContext(
        recall_id="recall_contract_test",
        timestamp="2026-06-09T15:00:00+00:00",
        query_type="text",
        query_summary="contract test",
        query_hash="sha256:contract",
        initiating_agent="pytest",
        source_node="test-node",
        vector_backend="none",
        embedding_model="none",
        ranking_method="contract_test_ranking",
        replay_reference={
            "available": True,
            "replay_id": "replay_contract_test",
            "source_path": "tests/test_recall_backend_contract.py",
            "timestamp": "2026-06-09T15:00:00+00:00",
            "reason": "",
        },
    )


def test_interface_importability() -> None:
    assert RecallBackend is not None
    assert RecallResult is not None
    assert RecallFilter is not None


def test_safety_default_values() -> None:
    assert base.SAFETY_DEFAULTS == {
        "guardian_visible": True,
        "decision_allowed": False,
        "action_allowed": False,
        "no_decision_made": True,
    }
    provenance = RecallProvenance(backend="fake")
    result = RecallResult(
        record_id="mem_test",
        score=0.5,
        rank=1,
        backend="fake",
        embedding_model="none",
        provenance=provenance,
    )
    assert result.decision_allowed is False
    assert result.action_allowed is False


def test_evidence_export_shape_matches_schema() -> None:
    backend = FakeRecallBackend()
    backend.add_record({"record_id": "mem_contract_test"})
    filters = RecallFilter(
        privacy_class=["internal"],
        governance_state=["raw"],
        tags=["contract"],
    )
    results = backend.query(None, filters, limit=1)
    evidence = backend.export_evidence(_query_context(), results, filters=filters)

    assert evidence["guardian_visible"] is True
    assert evidence["decision_allowed"] is False
    assert evidence["action_allowed"] is False
    assert evidence["no_decision_made"] is True
    assert evidence["candidate_record_ids"] == ["mem_contract_test"]

    schema = json.loads(Path("schemas/recall_evidence.schema.json").read_text())
    Draft202012Validator(schema).validate(evidence)


def test_failure_evidence_shape_matches_schema() -> None:
    evidence = failure_evidence(_query_context(), "contract test failure")
    assert evidence["candidate_record_ids"] == []
    assert evidence["decision_allowed"] is False
    assert evidence["action_allowed"] is False

    schema = json.loads(Path("schemas/recall_evidence.schema.json").read_text())
    Draft202012Validator(schema).validate(evidence)


def test_tombstone_method_existence() -> None:
    backend = FakeRecallBackend()
    result = backend.tombstone("mem_contract_test", "contract test")
    assert result["tombstoned"] is True
    assert "tombstone" in dir(RecallBackend)


def test_capabilities_method_existence() -> None:
    backend = FakeRecallBackend()
    caps = backend.capabilities()
    assert caps["supports_tombstones"] is True
    assert caps["supports_evidence_export"] is True
    assert "capabilities" in dir(RecallBackend)


def test_backend_neutrality() -> None:
    source = inspect.getsource(base).casefold()
    assert "turbovec" not in source
    assert "ryancodrai" not in source
    assert "turboquant" not in source

