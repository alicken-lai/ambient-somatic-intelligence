"""Validate DMN events against the v0.9 event taxonomy."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "dmn_event.schema.json"
DEFAULT_DMN = ROOT / "memory" / "dmn.jsonl"
DEFAULT_REPORT = ROOT / "reports" / "dmn_event_validation_report.json"


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_legacy_event(record: dict[str, Any]) -> str:
    text = json.dumps(record, ensure_ascii=False).lower()
    if "guardian" in text:
        return "GUARDIAN_EVENT"
    if "phase 8" in text or "reality" in text:
        return "REALITY_EVENT"
    if "phase 9" in text or "identity" in text or "continuity" in text:
        return "IDENTITY_EVENT"
    if "audit" in text or "release" in text:
        return "GOVERNANCE_EVENT"
    if "telemetry" in text or "system_state" in text:
        return "SYSTEM_EVENT"
    if "failure" in text or "failed" in text:
        return "FAILURE_EVENT"
    return "SYSTEM_EVENT"


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    content = record.get("content")
    if not isinstance(content, str):
        content = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return {
        **record,
        "event_type": record.get("event_type") or classify_legacy_event(record),
        "content": content,
        "timestamp": str(record.get("timestamp", "")),
    }


def validate_dmn(path: Path = DEFAULT_DMN, schema_path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    total = 0
    valid = 0
    errors: list[dict[str, Any]] = []
    event_types: Counter[str] = Counter()
    missing_timestamp = 0
    if not path.is_file():
        return {"path": str(path), "total": 0, "valid": 0, "errors": [{"line": 0, "message": "DMN file not found"}], "event_types": {}}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        total += 1
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_no, "message": str(exc)})
            continue
        if not isinstance(raw, dict):
            errors.append({"line": line_no, "message": "record is not an object"})
            continue
        normalized = normalize_record(raw)
        event_types[normalized["event_type"]] += 1
        if not normalized.get("timestamp"):
            missing_timestamp += 1
        record_errors = sorted(validator.iter_errors(normalized), key=lambda item: item.path)
        if record_errors:
            errors.extend({"line": line_no, "message": error.message} for error in record_errors[:3])
        else:
            valid += 1
    return {
        "path": str(path),
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "missing_timestamp": missing_timestamp,
        "event_types": dict(sorted(event_types.items())),
        "errors": errors[:50],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DMN events against Hermes-ASI taxonomy.")
    parser.add_argument("--dmn", default=str(DEFAULT_DMN))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--output", default=str(DEFAULT_REPORT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = validate_dmn(Path(args.dmn), Path(args.schema))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Validation report: {output}")
        print(f"Valid: {payload['valid']}/{payload['total']}")
    return 0 if payload["invalid"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
