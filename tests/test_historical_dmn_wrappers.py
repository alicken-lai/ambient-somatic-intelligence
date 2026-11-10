import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples" / "historical_dmn_wrappers"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wrapper_validator() -> Draft202012Validator:
    memory_schema = load_json(SCHEMAS / "memory_event.schema.json")
    wrapper_schema = load_json(SCHEMAS / "governed_memory_wrapper.schema.json")
    registry = Registry().with_resources(
        [
            ("memory_event.schema.json", Resource.from_contents(memory_schema)),
            (memory_schema["$id"], Resource.from_contents(memory_schema)),
        ]
    )
    Draft202012Validator.check_schema(wrapper_schema)
    return Draft202012Validator(wrapper_schema, registry=registry)


def historical_wrappers() -> list[Path]:
    return sorted(EXAMPLES.glob("historical_wrapper_*.example.json"))


def test_historical_wrappers_validate() -> None:
    v = wrapper_validator()
    wrappers = historical_wrappers()
    assert len(wrappers) == 3
    for path in wrappers:
        v.validate(load_json(path))


def test_historical_wrappers_do_not_mutate_memory() -> None:
    for path in historical_wrappers():
        wrapper = load_json(path)
        assert wrapper["audit"]["no_mutation"] is True
        assert wrapper["audit"]["validation_status"] == "validated"


def test_historical_wrappers_expose_replay_gap() -> None:
    for path in historical_wrappers():
        wrapper = load_json(path)
        replay = wrapper["audit"]["replay_pointer"]
        assert replay["available"] is False
        assert replay["reason"]


def test_sensitive_telemetry_is_not_sync_eligible() -> None:
    telemetry = load_json(EXAMPLES / "historical_wrapper_002.example.json")
    assert telemetry["governance_metadata"]["privacy_class"] == "sensitive"
    assert telemetry["governance_metadata"]["sync_eligibility"] == "not_eligible_sensitive"
    assert "52-0A40237-H2.local" not in telemetry["memory_event"]["summary"]
    assert "memory_usage" not in telemetry["memory_event"]["summary"]
