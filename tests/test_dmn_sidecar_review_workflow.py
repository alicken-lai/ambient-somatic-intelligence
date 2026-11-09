import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "dmn_sidecar_review.schema.json"
EXAMPLES = ROOT / "examples" / "dmn_sidecar_review"
PROPOSALS = ROOT / "reports" / "dmn_audit" / "dmn_metadata_sidecar_proposals.jsonl"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def review_examples() -> list[Path]:
    return sorted(EXAMPLES.glob("*_sidecar_review.example.json"))


def test_review_examples_validate_against_schema() -> None:
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    examples = review_examples()
    assert len(examples) == 4
    for path in examples:
        validator.validate(load_json(path))


def test_approved_example_is_indexing_only_not_sync() -> None:
    review = load_json(EXAMPLES / "approved_sidecar_review.example.json")
    assert review["review_state"] == "approved"
    assert review["audit"]["approved_for_indexing"] is True
    assert review["audit"]["approved_for_sync"] is False
    assert review["approval_gates"]["indexing_gate_passed"] is True
    assert review["approval_gates"]["sync_gate_passed"] is False


def test_rejected_and_revision_examples_block_all_use() -> None:
    for name in [
        "rejected_sidecar_review.example.json",
        "requires_revision_sidecar_review.example.json",
        "superseded_sidecar_review.example.json",
    ]:
        review = load_json(EXAMPLES / name)
        assert review["audit"]["approved_for_indexing"] is False
        assert review["audit"]["approved_for_sync"] is False


def test_guardian_reviewer_does_not_authorize_alone() -> None:
    review = load_json(EXAMPLES / "approved_sidecar_review.example.json")
    assert "guardian_reviewer" in review["reviewer_roles"]
    assert "owner" in review["reviewer_roles"]
    assert review["decisions"][0]["decided_by"] == "owner"


def test_real_sidecar_proposals_remain_unapproved() -> None:
    proposals = [
        json.loads(line)
        for line in PROPOSALS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert proposals
    assert all(proposal["review"]["approved"] is False for proposal in proposals)
    assert all(proposal["audit"]["proposal_only"] is True for proposal in proposals)
