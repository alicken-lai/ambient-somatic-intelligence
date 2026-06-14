import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "dmn_metadata_sidecar.schema.json"
REPORT_DIR = ROOT / "reports" / "dmn_audit"
SIDECAR_PATH = REPORT_DIR / "dmn_metadata_sidecar_proposals.jsonl"


def run_generator() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "propose_dmn_metadata_sidecars.py")],
        cwd=ROOT,
        check=True,
    )


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_sidecars() -> list[dict]:
    return [
        json.loads(line)
        for line in SIDECAR_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_sidecar_proposals_validate_against_schema() -> None:
    run_generator()
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    sidecars = load_sidecars()
    assert len(sidecars) == 50
    for sidecar in sidecars:
        validator.validate(sidecar)


def test_sidecars_are_proposal_only_and_unapproved() -> None:
    run_generator()
    for sidecar in load_sidecars():
        assert sidecar["audit"]["no_mutation"] is True
        assert sidecar["audit"]["proposal_only"] is True
        assert sidecar["review"]["approved"] is False


def test_sidecars_attach_by_line_and_hash() -> None:
    run_generator()
    for sidecar in load_sidecars():
        assert sidecar["source_file"] == "memory/dmn.jsonl"
        assert isinstance(sidecar["source_line"], int)
        assert sidecar["source_line"] > 0
        assert sidecar["source_hash"].startswith("sha256:")
        assert sidecar["source_record_id"] == f"memory/dmn.jsonl:{sidecar['source_line']}"


def test_reports_are_generated_and_state_proposal_status() -> None:
    run_generator()
    coverage = (REPORT_DIR / "dmn_metadata_sidecar_coverage_report.md").read_text(encoding="utf-8")
    queue = (REPORT_DIR / "dmn_metadata_sidecar_review_queue.md").read_text(encoding="utf-8")
    assert "proposal" in coverage.lower()
    assert "not as approved truth" in coverage
    assert "Records requiring review" in queue
