import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples" / "dmn_governance"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def registry() -> Registry:
    memory_schema = load_json(SCHEMAS / "memory_event.schema.json")
    return Registry().with_resources(
        [
            ("memory_event.schema.json", Resource.from_contents(memory_schema)),
            (memory_schema["$id"], Resource.from_contents(memory_schema)),
        ]
    )


def validator(schema_name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS / schema_name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry())


def wrapper_examples() -> list[Path]:
    return [
        EXAMPLES / "promoted_memory.example.json",
        EXAMPLES / "decayed_memory.example.json",
        EXAMPLES / "consolidated_memory.example.json",
        EXAMPLES / "conflicted_memory_a.example.json",
        EXAMPLES / "conflicted_memory_b.example.json",
    ]


def test_governed_memory_wrapper_examples_validate() -> None:
    v = validator("governed_memory_wrapper.schema.json")
    for path in wrapper_examples():
        v.validate(load_json(path))


def test_sync_manifest_example_validates_and_is_dry_run() -> None:
    v = validator("dmn_sync_manifest.schema.json")
    manifest = load_json(EXAMPLES / "sync_manifest_home_to_office.example.json")
    v.validate(manifest)

    assert manifest["sync_mode"] == "dry_run"
    assert manifest["no_mutation"] is True
    assert manifest["audit"]["actual_records_mutated"] == 0


def test_wrappers_keep_no_mutation_safety_default() -> None:
    for path in wrapper_examples():
        wrapper = load_json(path)
        assert wrapper["audit"]["no_mutation"] is True


def test_conflict_register_allows_unresolved_state() -> None:
    conflict_a = load_json(EXAMPLES / "conflicted_memory_a.example.json")
    conflict_b = load_json(EXAMPLES / "conflicted_memory_b.example.json")
    group_id = conflict_a["lineage"]["conflict_group_id"]

    register_entry = {
        "conflict_id": group_id,
        "schema_version": "1.0.0",
        "created_at": "2026-06-10T03:00:00Z",
        "created_by": "codex-tests",
        "conflict_type": "source_conflict",
        "status": "open",
        "claims": [
            {
                "claim_id": "claim-home-power-fluctuation",
                "record_id": conflict_a["memory_event"]["record_id"],
                "source_node": conflict_a["memory_event"]["source_node"],
                "claim_summary": conflict_a["governance_metadata"]["competing_claim"],
                "confidence": conflict_a["memory_event"]["confidence"],
                "evidence_ref": conflict_a["memory_event"]["content_ref"],
                "replay_pointer": conflict_a["audit"]["replay_pointer"],
            },
            {
                "claim_id": "claim-office-no-power-fluctuation",
                "record_id": conflict_b["memory_event"]["record_id"],
                "source_node": conflict_b["memory_event"]["source_node"],
                "claim_summary": conflict_b["governance_metadata"]["competing_claim"],
                "confidence": conflict_b["memory_event"]["confidence"],
                "evidence_ref": conflict_b["memory_event"]["content_ref"],
                "replay_pointer": conflict_b["audit"]["replay_pointer"],
            },
        ],
        "affected_record_ids": [
            conflict_a["memory_event"]["record_id"],
            conflict_b["memory_event"]["record_id"],
        ],
        "source_nodes": ["home-hermes", "office-hermes"],
        "confidence_summary": {
            "min_confidence": 0.69,
            "max_confidence": 0.73,
            "confidence_gap": 0.04,
            "summary": "Confidence gap is not sufficient for automatic resolution.",
        },
        "requires_review": True,
        "review_owner": "human-or-guardian-review",
        "resolution": {
            "resolution_status": "unresolved",
            "resolution_method": "",
            "resolved_claim_id": None,
            "resolution_reason": "Conflict is intentionally unresolved in dry-run examples.",
            "resolved_at": None,
            "resolved_by": None,
        },
        "audit": {
            "decision_log_ref": "docs/decision_logs/2026-06-10-dmn-governance-contract-schemas.md",
            "validation_status": "validated",
            "no_mutation": True,
        },
    }

    v = validator("dmn_conflict_register.schema.json")
    v.validate(register_entry)
    assert register_entry["resolution"]["resolution_status"] == "unresolved"


def test_contracts_do_not_require_turbovec() -> None:
    checked_paths = [
        SCHEMAS / "governed_memory_wrapper.schema.json",
        SCHEMAS / "dmn_conflict_register.schema.json",
        SCHEMAS / "dmn_sync_manifest.schema.json",
        *wrapper_examples(),
        EXAMPLES / "sync_manifest_home_to_office.example.json",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in checked_paths)
    assert "TurboVec" not in combined
    assert "turbovec" not in combined.lower()
