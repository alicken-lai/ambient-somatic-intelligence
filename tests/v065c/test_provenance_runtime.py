"""Area 5: Runtime provenance validation."""

from governance.external.runtime.runtime_provenance_validator import RuntimeProvenanceValidator


def test_provenance_good_text() -> None:
    val = RuntimeProvenanceValidator()
    assert val.validate(
        "skill_id: karpathy_guidelines source: github mount_version: 0.6.5b"
    ).valid


def test_provenance_bad_text() -> None:
    val = RuntimeProvenanceValidator()
    assert not val.validate("No provenance here.").valid
