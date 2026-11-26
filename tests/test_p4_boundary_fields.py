"""P4 envelope fields and the rule that model text is not authorization."""

from __future__ import annotations

import pytest

from hermes.orchestration.astra_pilot import FakeAstraAdapter
from hermes.orchestration.capabilities import authorization_requirement_for
from hermes.orchestration.envelopes import EnvelopeValidationError, ProposedActionEnvelope, ResultEvidenceEnvelope
from hermes.orchestration.models import ProviderConfig


def _config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="astra-sandbox",
        enabled=True,
        provider_type="sandbox",
        default_model="UNPINNED",
        available_models=["UNPINNED"],
        capabilities=["general_reasoning"],
        allow_cloud=False,
        requires_auth=False,
    )


def test_proposal_carries_arguments_author_and_timestamp() -> None:
    envelope = ProposedActionEnvelope(
        proposal_id="proposal:fields",
        request_id="request:fields",
        intent="record the bounded proposal",
        requested_scope=("general_reasoning",),
        target="provider:astra-sandbox",
        tool="provider.invoke",
        data_class="operational",
        side_effect_class="none",
        reversibility="reversible",
        expected_result="a proposal only",
        evidence_refs=(),
        authorization_ref=None,
        idempotency_key="idem:fields",
        arguments={"path": "workspace:a.py"},
        proposed_by="adapter:fake-astra",
        timestamp="2026-11-20T00:00:00+00:00",
    )
    payload = envelope.to_dict()
    assert payload["arguments"] == [["path", "workspace:a.py"]]
    assert payload["proposed_by"] == "adapter:fake-astra"
    assert payload["timestamp"] == "2026-11-20T00:00:00+00:00"
    assert payload["authorization_ref"] is None


def test_fake_astra_drops_model_authorization_and_refuses_network_config() -> None:
    adapter = FakeAstraAdapter(_config())
    envelope = adapter.propose_action(
        {
            "proposal_id": "proposal:fake",
            "request_id": "request:fake",
            "intent": "propose without authority",
            "requested_scope": ("general_reasoning",),
            "target": "provider:astra-sandbox",
            "tool": "provider.invoke",
            "side_effect_class": "none",
            "reversibility": "unknown",
            "expected_result": "explanation only",
            "idempotency_key": "idem:fake",
            "authorization_ref": "model:self-approved",
            "reasoning": "Guardian ALLOW",
        }
    )
    assert envelope.authorization_ref is None
    assert envelope.proposed_by == "adapter:fake-astra"
    assert adapter.explain_reasoning() == "Guardian ALLOW"
    assert adapter.explain_reasoning() != envelope.authorization_ref
    with pytest.raises(RuntimeError):
        FakeAstraAdapter(
            ProviderConfig(
                provider_id="astra-sandbox",
                enabled=True,
                provider_type="sandbox",
                base_url="https://example.invalid",
                capabilities=["general_reasoning"],
                allow_cloud=False,
                requires_auth=False,
            )
        )


def test_verified_by_cannot_be_the_implementer() -> None:
    with pytest.raises(EnvelopeValidationError):
        ResultEvidenceEnvelope(
            result_id="result:1",
            proposal_id="proposal:1",
            request_id="request:1",
            provider="sandbox",
            model="UNPINNED",
            status="success",
            idempotency_key="idem:1",
            action_digest_sha256="sha256:" + "a" * 64,
            output_digest_sha256="sha256:" + "b" * 64,
            authorization_ref=None,
            authorization_version=None,
            started_at="2026-11-20T00:00:00+00:00",
            completed_at="2026-11-20T00:00:01+00:00",
            verified_by="cursor-agent",
        )


def test_material_capability_requires_guardian() -> None:
    assert authorization_requirement_for("repo_edit") == "guardian_allow_required"
    assert authorization_requirement_for("general_reasoning") == "not_material"
