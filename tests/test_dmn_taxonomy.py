import json
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.validate_dmn_events import normalize_record, validate_dmn


ROOT = Path(__file__).resolve().parents[1]


def test_dmn_event_schema_accepts_canonical_event() -> None:
    schema = json.loads((ROOT / "schemas" / "dmn_event.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    event = {
        "event_type": "REALITY_EVENT",
        "content": "Reality score generated.",
        "timestamp": "2026-06-14T00:00:00Z",
        "producer_kernel": "reality_alignment",
        "consumer_kernels": ["identity", "audit"],
        "retention": "long",
    }
    validator.validate(event)


def test_legacy_dmn_record_is_normalized() -> None:
    normalized = normalize_record({"content": "Guardian allowed local audit.", "timestamp": "2026-06-14T00:00:00Z"})
    assert normalized["event_type"] == "GUARDIAN_EVENT"
    assert normalized["content"]


def test_dmn_validation_reports_statistics(tmp_path: Path) -> None:
    dmn = tmp_path / "dmn.jsonl"
    dmn.write_text(
        json.dumps({"event_type": "IDENTITY_EVENT", "content": "Identity report generated.", "timestamp": "2026-06-14T00:00:00Z"}) + "\n",
        encoding="utf-8",
    )
    payload = validate_dmn(dmn, ROOT / "schemas" / "dmn_event.schema.json")
    assert payload["total"] == 1
    assert payload["valid"] == 1
    assert payload["event_types"]["IDENTITY_EVENT"] == 1
