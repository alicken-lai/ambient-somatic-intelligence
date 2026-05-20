"""Area 3: External skill registry states."""

from hermes.skills.external.external_skill_status import ExternalSkillStatus


def test_registry_mounts_karpathy(external_registry) -> None:
    rec = external_registry.get("karpathy_guidelines")
    assert rec is not None
    assert rec.status in {
        ExternalSkillStatus.COMPATIBLE,
        ExternalSkillStatus.RESTRICTED,
    }
    assert rec.provenance_hash


def test_advisory_for_route(external_registry) -> None:
    adv = external_registry.advisory_for_route("attention_submit")
    assert adv["advisory_only"] is True
    assert adv["constitutional_supremacy"] is True
