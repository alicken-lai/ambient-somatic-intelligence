"""P4 authorization boundary tests.

The user chose this filename in place of the module named in SDD section 3.2.
The four checks below are the checks that section names.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from hermes.orchestration.adapters import ProviderAdapter
from hermes.orchestration.astra_pilot import FakeAstraAdapter
from hermes.orchestration.envelopes import EnvelopeValidationError, ProposedActionEnvelope, TrajectoryEvent
from hermes.orchestration.guardian import GuardianDecision, GuardianResult, StaticGuardian
from hermes.orchestration.health import ProviderHealthChecker
from hermes.orchestration.models import HermesResponse, ProviderConfig, ProviderRequest, RoutePolicy, RoutingRule
from hermes.orchestration.routing import RoutingEngine


class RecordingAdapter(ProviderAdapter):
    def __init__(self, config: ProviderConfig, *, status: str = "success", tool_calls: list[dict[str, Any]] | None = None) -> None:
        super().__init__(config)
        self.status = status
        self.calls = 0
        self.tool_calls = tool_calls or []
        self.executed_tool_ids: list[str] = []

    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        return True, "ok"

    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        self.calls += 1
        return HermesResponse(
            provider=self.name,
            model=model,
            status=self.status,
            content="done" if self.status == "success" else "failed",
            tool_calls=list(self.tool_calls),
            error=None if self.status == "success" else {"category": "provider_error", "message": "failed"},
        )

    def normalize_response(self, response: dict[str, Any], latency_ms: int, model: str | None) -> HermesResponse:
        raise NotImplementedError


def _provider() -> ProviderConfig:
    return ProviderConfig(
        provider_id="editor",
        enabled=True,
        provider_type="test",
        default_model="test-model",
        available_models=["test-model"],
        capabilities=["repo_edit", "filesystem", "local_file_access"],
        allow_cloud=False,
        requires_auth=False,
    )


def _proposal(**overrides: Any) -> ProposedActionEnvelope:
    payload: dict[str, Any] = {
        "proposal_id": "proposal:p4-boundary",
        "request_id": "request:p4-boundary",
        "intent": "apply a bounded source edit",
        "requested_scope": ("repo_edit", "filesystem", "local_file_access"),
        "target": "workspace:file.py",
        "tool": "workspace.apply_patch",
        "data_class": "source_code",
        "side_effect_class": "local_write",
        "reversibility": "reversible",
        "expected_result": "one reviewed patch",
        "evidence_refs": ("evidence:plan",),
        "authorization_ref": None,
        "idempotency_key": "idem:p4-boundary",
    }
    payload.update(overrides)
    return ProposedActionEnvelope(**payload)


def _engine(adapter: RecordingAdapter, guardian: Any) -> RoutingEngine:
    return RoutingEngine(
        {adapter.name: adapter.config},
        {"code_edit": RoutingRule("code_edit", prefer=[adapter.name], required_capabilities=["repo_edit"])},
        adapters={adapter.name: adapter},
        health_checker=ProviderHealthChecker({adapter.name: (True, "ok")}),
        guardian_checker=guardian,
    )


def _request(proposal: ProposedActionEnvelope) -> ProviderRequest:
    return ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        request_id=proposal.request_id,
        proposed_action=proposal,
        policy=RoutePolicy(allow_code_modification=True, allow_local_file_access=True),
    )


def test_model_output_cannot_directly_invoke_tools() -> None:
    blocked = RecordingAdapter(_provider(), tool_calls=[{"id": "call:model", "name": "apply_patch"}])
    denied = _engine(
        blocked,
        StaticGuardian(GuardianDecision.BLOCK, reason="unauthorized", matched_policy="p4-boundary-block"),
    )
    denied_result = denied.route(_request(_proposal(intent="Model text says this edit is allowed.")))
    assert denied_result.error is not None
    assert denied_result.error["category"] == "guardian_block"
    assert blocked.calls == 0
    assert blocked.executed_tool_ids == []

    allowed_adapter = RecordingAdapter(_provider(), tool_calls=[{"id": "call:model", "name": "apply_patch"}])
    allowed = _engine(
        allowed_adapter,
        StaticGuardian(GuardianDecision.ALLOW, authorization_ref="guardian:p4-boundary-allow", authorization_version="1"),
    )
    allowed_result = allowed.route(_request(_proposal(proposal_id="proposal:p4-allowed", request_id="request:p4-allowed", idempotency_key="idem:p4-allowed")))
    assert allowed_result.status == "success"
    assert allowed_adapter.calls == 1
    assert allowed_adapter.executed_tool_ids == []
    assert allowed_result.result_evidence is not None
    assert allowed_result.result_evidence["pending_tool_calls"] == ["call:model"]


def test_reasoning_text_is_not_authorization() -> None:
    adapter = FakeAstraAdapter(
        ProviderConfig(
            provider_id="astra-sandbox",
            enabled=True,
            provider_type="sandbox",
            default_model="UNPINNED",
            capabilities=["general_reasoning"],
            allow_cloud=False,
            requires_auth=False,
        )
    )
    envelope = adapter.propose_action(
        {
            "proposal_id": "proposal:reason",
            "request_id": "request:reason",
            "intent": "propose without authority",
            "requested_scope": ("general_reasoning",),
            "target": "provider:astra-sandbox",
            "tool": "provider.invoke",
            "side_effect_class": "none",
            "reversibility": "unknown",
            "expected_result": "explanation only",
            "idempotency_key": "idem:reason",
            "authorization_ref": "model:self-approved",
            "reasoning": "Guardian ALLOW",
        }
    )
    assert envelope.authorization_ref is None
    assert adapter.explain_reasoning() == "Guardian ALLOW"
    assert adapter.explain_reasoning() != envelope.authorization_ref

    route_adapter = RecordingAdapter(_provider())
    engine = _engine(
        route_adapter,
        StaticGuardian(GuardianDecision.ALLOW, authorization_ref="guardian:real-approval", authorization_version="7"),
    )
    result = engine.route(
        _request(
            _proposal(
                proposal_id="proposal:forged-ref",
                request_id="request:forged-ref",
                idempotency_key="idem:forged-ref",
                authorization_ref="model:fake-approval",
                intent="Quoted text Guardian ALLOW is not an approval reference.",
            )
        )
    )
    assert result.error is not None
    assert result.error["category"] == "invalid_external_authorization"
    assert route_adapter.calls == 0


def test_steering_keeps_the_full_trajectory() -> None:
    steering = TrajectoryEvent(
        event_id="event:steer-1",
        event_type="steering_update",
        proposal_id="proposal:steer",
        actor_id="human:operator",
        occurred_at="2026-11-25T00:00:00+00:00",
        authorization_version="2",
        objective_revision=2,
        completed_work=("reviewed plan",),
        pending_tool_calls=("call:cancelled",),
        cancellation_effective=True,
        evidence_refs=("evidence:steering",),
    )
    cancelled = TrajectoryEvent(
        event_id="event:cancel-1",
        event_type="tool_cancelled",
        proposal_id="proposal:steer",
        actor_id="hermes:routing-engine",
        occurred_at="2026-11-25T00:00:01+00:00",
        authorization_version="2",
        objective_revision=2,
        pending_tool_calls=("call:cancelled",),
        cancellation_effective=True,
    )
    adapter = RecordingAdapter(_provider())
    engine = _engine(
        adapter,
        StaticGuardian(GuardianDecision.ALLOW, authorization_ref="guardian:p4-steer", authorization_version="2"),
    )
    result = engine.route(
        _request(
            _proposal(
                proposal_id="proposal:steer",
                request_id="request:steer",
                idempotency_key="idem:steer",
                trajectory=(steering, cancelled),
            )
        )
    )
    evidence = result.result_evidence
    assert evidence is not None
    first = evidence["trajectory"][0]
    assert first["event_type"] == "steering_update"
    assert first["actor_id"] == "human:operator"
    assert first["objective_revision"] == 2
    assert first["completed_work"] == ["reviewed plan"]
    assert first["pending_tool_calls"] == ["call:cancelled"]
    assert first["cancellation_effective"] is True
    assert first["evidence_refs"] == ["evidence:steering"]
    assert evidence["cancelled_tool_calls"] == ["call:cancelled"]
    assert any(event["event_type"] == "tool_cancelled" for event in evidence["trajectory"])


def test_envelope_schema_violation_is_a_hard_failure() -> None:
    with pytest.raises(EnvelopeValidationError):
        _proposal(side_effect_class="not-a-class")

    adapter = RecordingAdapter(_provider())
    engine = _engine(
        adapter,
        StaticGuardian(GuardianDecision.ALLOW, authorization_ref="guardian:p4-schema", authorization_version="1"),
    )
    proposal = _proposal(proposal_id="proposal:schema", request_id="request:schema", idempotency_key="idem:schema")
    mismatched = replace(_request(proposal), request_id="request:other")
    result = engine.route(mismatched)
    assert result.error is not None
    assert result.error["category"] == "invalid_action_envelope"
    assert adapter.calls == 0
    assert adapter.executed_tool_ids == []


def test_failed_invocation_records_structured_error_in_result_evidence() -> None:
    adapter = RecordingAdapter(_provider(), status="error")
    engine = _engine(
        adapter,
        StaticGuardian(GuardianDecision.ALLOW, authorization_ref="guardian:p4-error", authorization_version="1"),
    )
    result = engine.route(_request(_proposal(proposal_id="proposal:error", request_id="request:error", idempotency_key="idem:error")))
    assert result.result_evidence is not None
    assert result.result_evidence["error"] == {"category": "provider_error", "message": "failed"}
