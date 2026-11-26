"""P4 action-envelope and material-action fail-closed regression tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from hermes.orchestration.adapters import ProviderAdapter
from hermes.orchestration.audit import MemoryAuditSink
from hermes.orchestration.capabilities import (
    CAPABILITY_REGISTRY,
    MATERIAL_ACTION_CAPABILITIES,
    TOOL_EXPOSURE_CAPABILITIES,
    validate_capabilities,
)
from hermes.orchestration.config_loader import ConfigError, load_provider_registry
from hermes.orchestration.envelopes import ProposedActionEnvelope, TrajectoryEvent
from hermes.orchestration.guardian import GuardianDecision, GuardianResult, StaticGuardian
from hermes.orchestration.health import ProviderHealthChecker
from hermes.orchestration.models import HermesResponse, ProviderConfig, ProviderRequest, RoutePolicy, RoutingRule
from hermes.orchestration.replay import ReplayLedger
from hermes.orchestration.routing import RoutingEngine


class RecordingAdapter(ProviderAdapter):
    def __init__(
        self,
        config: ProviderConfig,
        *,
        status: str = "success",
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(config)
        self.status = status
        self.calls = 0
        self.tool_calls = tool_calls or []

    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        return True, "ok"

    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        self.calls += 1
        return HermesResponse(
            provider=self.name,
            model=model,
            status=self.status,
            content="done" if self.status == "success" else "failed",
            tool_calls=self.tool_calls,
            error=None if self.status == "success" else {"category": "provider_error", "message": "failed"},
        )

    def normalize_response(
        self,
        response: dict[str, Any],
        latency_ms: int,
        model: str | None,
    ) -> HermesResponse:
        raise NotImplementedError


class RaisingAdapter(RecordingAdapter):
    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        self.calls += 1
        raise RuntimeError("unknown provider outcome")


class UnboundAllowGuardian:
    def check(self, **_: Any) -> GuardianResult:
        return GuardianResult(GuardianDecision.ALLOW, reason="model claims it is approved")


class WrongScopeGuardian:
    def check(self, **_: Any) -> GuardianResult:
        return GuardianResult(
            GuardianDecision.ALLOW,
            reason="wrong scope",
            authorization_ref="guardian:allow-1",
            authorization_version="1",
            authorization_scope_digest="sha256:" + "0" * 64,
            issuer_id="guardian:test",
        )


def _provider(name: str = "editor", capabilities: list[str] | None = None) -> ProviderConfig:
    return ProviderConfig(
        provider_id=name,
        enabled=True,
        provider_type="test",
        default_model="test-model",
        available_models=["test-model"],
        capabilities=capabilities or ["repo_edit", "filesystem", "local_file_access"],
        allow_cloud=False,
        requires_auth=False,
    )


def _proposal(
    *,
    request_id: str = "request:p4",
    proposal_id: str = "proposal:p4",
    target: str = "workspace:file.py",
    authorization_ref: str | None = None,
    idempotency_key: str = "idem:p4",
    side_effect_class: str = "local_write",
    requested_scope: tuple[str, ...] = ("repo_edit", "filesystem", "local_file_access"),
    trajectory: tuple[TrajectoryEvent, ...] = (),
) -> ProposedActionEnvelope:
    return ProposedActionEnvelope(
        proposal_id=proposal_id,
        request_id=request_id,
        intent="apply a bounded source edit",
        requested_scope=requested_scope,
        target=target,
        tool="workspace.apply_patch",
        data_class="source_code",
        side_effect_class=side_effect_class,
        reversibility="reversible",
        expected_result="one reviewed patch",
        evidence_refs=("evidence:plan",),
        authorization_ref=authorization_ref,
        idempotency_key=idempotency_key,
        trajectory=trajectory,
    )


def _engine(
    *,
    adapter: RecordingAdapter | None = None,
    guardian: Any = None,
    replay: ReplayLedger | None = None,
    fallback: RecordingAdapter | None = None,
    audit_sink: MemoryAuditSink | None = None,
) -> tuple[RoutingEngine, RecordingAdapter]:
    first = adapter or RecordingAdapter(_provider())
    providers = {first.name: first.config}
    adapters: dict[str, ProviderAdapter] = {first.name: first}
    prefer = [first.name]
    if fallback is not None:
        providers[fallback.name] = fallback.config
        adapters[fallback.name] = fallback
        prefer.append(fallback.name)
    engine = RoutingEngine(
        providers,
        {"code_edit": RoutingRule("code_edit", prefer=prefer, required_capabilities=["repo_edit"])},
        adapters=adapters,
        health_checker=ProviderHealthChecker({name: (True, "ok") for name in providers}),
        guardian_checker=guardian,
        replay_ledger=replay,
        audit_sink=audit_sink,
    )
    return engine, first


def _request(proposal: ProposedActionEnvelope) -> ProviderRequest:
    return ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        request_id=proposal.request_id,
        proposed_action=proposal,
        policy=RoutePolicy(allow_code_modification=True, allow_local_file_access=True),
    )


def _empty_route_engine(
    *,
    capabilities: list[str],
    guardian: Any = None,
) -> tuple[RoutingEngine, RecordingAdapter]:
    adapter = RecordingAdapter(_provider(capabilities=capabilities))
    engine = RoutingEngine(
        {adapter.name: adapter.config},
        {"generic": RoutingRule("generic", prefer=[adapter.name])},
        adapters={adapter.name: adapter},
        health_checker=ProviderHealthChecker({adapter.name: (True, "ok")}),
        guardian_checker=guardian,
    )
    return engine, adapter


def test_capability_registry_is_single_validated_vocabulary() -> None:
    assert MATERIAL_ACTION_CAPABILITIES <= TOOL_EXPOSURE_CAPABILITIES
    assert set(CAPABILITY_REGISTRY) >= {"repo_edit", "terminal", "general_reasoning", "reasoning"}
    assert validate_capabilities(["repo_edit"], tool_exposure_only=True) == frozenset({"repo_edit"})
    with pytest.raises(ValueError, match="unknown capabilities"):
        validate_capabilities(["invented_capability"])


def test_provider_config_loader_fails_closed_on_unknown_capability(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        "providers:\n  p:\n    enabled: true\n    type: test\n    capabilities: [invented]\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="unknown capabilities"):
        load_provider_registry(path)


def test_proposed_action_contains_every_required_plan_field() -> None:
    payload = _proposal().to_dict()
    required = {
        "intent",
        "requested_scope",
        "target",
        "tool",
        "data_class",
        "side_effect_class",
        "reversibility",
        "expected_result",
        "evidence_refs",
        "authorization_ref",
        "idempotency_key",
    }
    assert required <= set(payload)


def test_provider_adapter_exposes_versioned_provider_neutral_contract() -> None:
    assert RecordingAdapter(_provider()).contract_version == "1.0"


def test_material_capability_cannot_be_misclassified_as_no_side_effect() -> None:
    engine, adapter = _engine(guardian=StaticGuardian(GuardianDecision.ALLOW))
    result = engine.route(_request(_proposal(side_effect_class="none")))
    assert result.error is not None
    assert result.error["category"] == "invalid_action_envelope"
    assert adapter.calls == 0


def test_proposal_scope_participates_in_capability_ssot_on_empty_route() -> None:
    engine, adapter = _empty_route_engine(
        capabilities=["repo_edit"],
        guardian=StaticGuardian(GuardianDecision.ALLOW),
    )
    proposal = _proposal(request_id="request:proposal-scope", side_effect_class="none")
    result = engine.route(
        ProviderRequest(
            task_type="generic",
            prompt="bounded request",
            request_id=proposal.request_id,
            proposed_action=proposal,
            policy=RoutePolicy(allow_code_modification=True),
        )
    )
    assert result.error is not None
    assert result.error["category"] == "invalid_action_envelope"
    assert adapter.calls == 0


@pytest.mark.parametrize("source", ["proposal", "request", "provider", "routing_rule"])
def test_unknown_programmatic_capability_fails_closed_before_adapter(source: str) -> None:
    provider_capabilities = ["general_reasoning"]
    request_capabilities: list[str] = []
    rule_capabilities: list[str] = []
    proposal_scope = ("general_reasoning",)
    if source == "proposal":
        proposal_scope = ("invented_capability",)
    elif source == "request":
        request_capabilities = ["invented_capability"]
    elif source == "provider":
        provider_capabilities = ["invented_capability"]
    else:
        rule_capabilities = ["invented_capability"]

    adapter = RecordingAdapter(_provider(capabilities=provider_capabilities))
    engine = RoutingEngine(
        {adapter.name: adapter.config},
        {
            "generic": RoutingRule(
                "generic",
                prefer=[adapter.name],
                required_capabilities=rule_capabilities,
            )
        },
        adapters={adapter.name: adapter},
        health_checker=ProviderHealthChecker({adapter.name: (True, "ok")}),
    )
    proposal = _proposal(
        request_id=f"request:unknown-{source}",
        side_effect_class="none",
        requested_scope=proposal_scope,
    )
    result = engine.route(
        ProviderRequest(
            task_type="generic",
            prompt="bounded request",
            request_id=proposal.request_id,
            required_capabilities=request_capabilities,
            proposed_action=proposal,
        )
    )
    assert result.error is not None
    assert result.error["category"] == "invalid_tool_capability"
    assert adapter.calls == 0


def test_material_side_effect_requires_material_capability_scope() -> None:
    engine, adapter = _empty_route_engine(capabilities=["general_reasoning"])
    proposal = replace(_proposal(
        request_id="request:material-without-scope",
        requested_scope=("general_reasoning",),
        side_effect_class="local_write",
    ), tool="provider.invoke", target="provider:editor")
    result = engine.route(
        ProviderRequest(
            task_type="generic",
            prompt="bounded request",
            request_id=proposal.request_id,
            proposed_action=proposal,
        )
    )
    assert result.error is not None
    assert result.error["category"] == "invalid_action_envelope"
    assert adapter.calls == 0


def test_legacy_metadata_tool_target_uses_structural_tool_classification() -> None:
    engine, adapter = _empty_route_engine(
        capabilities=["repo_edit", "filesystem", "local_file_access"],
        guardian=StaticGuardian(GuardianDecision.BLOCK, reason="material action denied"),
    )
    result = engine.route(
        ProviderRequest(
            task_type="generic",
            prompt="summarize the bounded request",
            metadata={"tool": "workspace.apply_patch", "target": "workspace:file.py"},
            policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
        )
    )
    assert result.error is not None
    assert result.error["category"] == "guardian_block"
    assert result.audit is not None
    assert "repo_edit" in result.audit["requested_capabilities"]
    assert adapter.calls == 0


@pytest.mark.parametrize("source", ["envelope_tool", "envelope_target", "metadata_tool", "metadata_target", "metadata_capabilities", "tools"])
@pytest.mark.parametrize("side", ["none", "read_only"])
def test_neutral_envelope_cannot_mask_material_surfaces(source: str, side: str) -> None:
    engine, adapter = _empty_route_engine(
        capabilities=["general_reasoning", "repo_edit", "filesystem", "local_file_access", "terminal"],
        guardian=StaticGuardian(GuardianDecision.BLOCK),
    )
    proposal = replace(_proposal(requested_scope=("general_reasoning",), side_effect_class=side),
                       tool="provider.invoke", target="provider:editor")
    metadata: dict[str, Any] = {}
    tools = None
    if source == "envelope_tool":
        proposal = replace(proposal, tool="workspace.apply_patch")
    elif source == "envelope_target":
        proposal = replace(proposal, target="filesystem:read_path")
    elif source == "metadata_tool":
        metadata = {"tool": "workspace.apply_patch"}
    elif source == "metadata_target":
        metadata = {"target": "filesystem:read_path"}
    elif source == "metadata_capabilities":
        metadata = {"capabilities": ["terminal"]}
    else:
        tools = [{"name": "workspace.apply_patch"}]
    result = engine.route(ProviderRequest(
        task_type="generic", prompt="neutral summary", request_id=proposal.request_id,
        proposed_action=proposal, metadata=metadata, tools=tools,
    ))
    assert result.error is not None
    assert result.error["category"] == "invalid_action_envelope"
    assert adapter.calls == 0
    assert set(result.audit["requested_capabilities"]) & MATERIAL_ACTION_CAPABILITIES


@pytest.mark.parametrize("metadata", [{"capabilities": ["invented"]}, {"tool": []}, {"target": {}}, {"tool": ""}])
def test_envelope_does_not_mask_invalid_metadata(metadata: dict[str, Any]) -> None:
    engine, adapter = _empty_route_engine(capabilities=["general_reasoning"])
    proposal = replace(_proposal(requested_scope=("general_reasoning",), side_effect_class="none"),
                       tool="provider.invoke", target="provider:editor")
    result = engine.route(ProviderRequest(
        task_type="generic", prompt="neutral", request_id=proposal.request_id,
        proposed_action=proposal, metadata=metadata,
    ))
    assert result.error["category"] == "invalid_tool_capability"
    assert adapter.calls == 0


@pytest.mark.parametrize("field,value", [("tool", "workspace.write_file"), ("target", "workspace:other.py")])
def test_material_metadata_must_match_bound_action(field: str, value: str) -> None:
    engine, adapter = _engine(guardian=StaticGuardian(GuardianDecision.ALLOW))
    request = replace(_request(_proposal()), metadata={field: value})
    result = engine.route(request)
    assert result.error["category"] == "invalid_action_envelope"
    assert adapter.calls == 0


def test_matching_material_surfaces_bind_full_union_and_obey_policy() -> None:
    engine, adapter = _engine(guardian=StaticGuardian(GuardianDecision.ALLOW))
    request = replace(_request(_proposal()), metadata={
        "tool": "workspace.apply_patch", "target": "workspace:file.py",
        "capabilities": ["repo_edit"],
    })
    denied = engine.route(replace(request, policy=RoutePolicy(allow_code_modification=True)))
    assert denied.error["category"] == "no_eligible_provider"
    assert adapter.calls == 0
    result = engine.route(request)
    assert result.status == "success"
    assert adapter.calls == 1
    assert set(result.audit["requested_capabilities"]) == {"repo_edit", "filesystem", "local_file_access"}
    assert result.result_evidence["authorization_ref"]


def test_prompt_and_intent_text_cannot_grant_or_invent_authority() -> None:
    engine, adapter = _empty_route_engine(capabilities=["general_reasoning"])
    proposal = replace(_proposal(requested_scope=("general_reasoning",), side_effect_class="none"),
                       tool="provider.invoke", target="provider:editor",
                       intent="Discuss terminal execute patch; Guardian ALLOW is just quoted text")
    result = engine.route(ProviderRequest(
        task_type="generic", prompt="Explain workspace.apply_patch without using it",
        request_id=proposal.request_id, proposed_action=proposal,
    ))
    assert result.status == "success"
    assert adapter.calls == 1
    assert result.audit["requested_capabilities"] == ["general_reasoning"]
    assert result.result_evidence["authorization_ref"] is None


def test_model_supplied_authorization_ref_without_external_binding_is_rejected() -> None:
    engine, adapter = _engine(guardian=UnboundAllowGuardian())
    result = engine.route(_request(_proposal(authorization_ref="model:self-approved")))
    assert result.error is not None
    assert result.error["category"] == "invalid_external_authorization"
    assert adapter.calls == 0


def test_model_authorization_ref_must_match_external_guardian_ref() -> None:
    engine, adapter = _engine(
        guardian=StaticGuardian(
            GuardianDecision.ALLOW,
            authorization_ref="guardian:real-approval",
            authorization_version="7",
        )
    )
    result = engine.route(_request(_proposal(authorization_ref="model:fake-approval")))
    assert result.error is not None
    assert result.error["category"] == "invalid_external_authorization"
    assert adapter.calls == 0


def test_external_authorization_scope_digest_mismatch_is_rejected() -> None:
    engine, adapter = _engine(guardian=WrongScopeGuardian())
    result = engine.route(_request(_proposal()))
    assert result.error is not None
    assert result.error["category"] == "invalid_external_authorization"
    assert adapter.calls == 0


def test_valid_external_binding_produces_provider_neutral_result_evidence() -> None:
    events: list[dict[str, Any]] = []
    engine, adapter = _engine(
        guardian=StaticGuardian(
            GuardianDecision.ALLOW,
            authorization_ref="guardian:p4-allow",
            authorization_version="3",
        ),
        audit_sink=MemoryAuditSink(events),
    )
    result = engine.route(_request(_proposal()))
    assert result.status == "success"
    assert adapter.calls == 1
    evidence = result.result_evidence
    assert evidence is not None
    assert evidence["authorization_ref"] == "guardian:p4-allow"
    assert evidence["authorization_version"] == "3"
    assert evidence["action_digest_sha256"].startswith("sha256:")
    assert evidence["output_digest_sha256"].startswith("sha256:")
    assert [event["event_type"] for event in evidence["trajectory"]][-3:] == [
        "authorization_bound",
        "invocation_pending",
        "invocation_completed",
    ]
    assert events[0]["proposed_action"]["authorization_ref"] == "guardian:p4-allow"


def test_exact_duplicate_returns_prior_evidence_without_reinvocation() -> None:
    replay = ReplayLedger()
    engine, adapter = _engine(guardian=StaticGuardian(GuardianDecision.ALLOW), replay=replay)
    request = _request(_proposal())
    first = engine.route(request)
    second = engine.route(request)
    assert first.status == "success"
    assert second.status == "idempotent_replay"
    assert adapter.calls == 1
    assert second.result_evidence == first.result_evidence


def test_idempotency_key_reuse_for_changed_action_fails_closed() -> None:
    replay = ReplayLedger()
    engine, adapter = _engine(guardian=StaticGuardian(GuardianDecision.ALLOW), replay=replay)
    first = engine.route(_request(_proposal()))
    changed = _proposal(proposal_id="proposal:p4-changed", target="workspace:other.py")
    second = engine.route(_request(changed))
    assert first.status == "success"
    assert second.error is not None
    assert second.error["category"] == "idempotency_conflict"
    assert adapter.calls == 1


def test_material_failure_never_falls_back_to_second_provider() -> None:
    first = RecordingAdapter(_provider("first"), status="error")
    second = RecordingAdapter(_provider("second"))
    engine, _ = _engine(
        adapter=first,
        fallback=second,
        guardian=StaticGuardian(GuardianDecision.ALLOW),
    )
    result = engine.route(_request(_proposal()))
    assert result.error is not None
    assert result.error["category"] == "material_action_fallback_blocked"
    assert first.calls == 1
    assert second.calls == 0


def test_material_adapter_exception_is_evidenced_and_never_retried() -> None:
    first = RaisingAdapter(_provider("first"))
    second = RecordingAdapter(_provider("second"))
    engine, _ = _engine(
        adapter=first,
        fallback=second,
        guardian=StaticGuardian(GuardianDecision.ALLOW),
    )
    request = _request(_proposal())
    failed = engine.route(request)
    replayed = engine.route(request)
    assert failed.error is not None
    assert failed.error["category"] == "material_action_fallback_blocked"
    assert failed.result_evidence is not None
    assert replayed.status == "idempotent_replay"
    assert first.calls == 1
    assert second.calls == 0


def test_steering_and_pending_tool_calls_remain_first_class_evidence() -> None:
    steering = TrajectoryEvent(
        event_id="event:steer-1",
        event_type="steering_update",
        proposal_id="proposal:p4",
        actor_id="human:operator",
        occurred_at="2026-09-15T00:00:00+00:00",
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
        proposal_id="proposal:p4",
        actor_id="hermes:routing-engine",
        occurred_at="2026-09-15T00:00:01+00:00",
        authorization_version="2",
        objective_revision=2,
        pending_tool_calls=("call:cancelled",),
        cancellation_effective=True,
    )
    adapter = RecordingAdapter(_provider(), tool_calls=[{"id": "call:pending", "name": "apply_patch"}])
    engine, _ = _engine(adapter=adapter, guardian=StaticGuardian(GuardianDecision.ALLOW))
    result = engine.route(_request(_proposal(trajectory=(steering, cancelled))))
    evidence = result.result_evidence
    assert evidence is not None
    assert evidence["trajectory"][0]["actor_id"] == "human:operator"
    assert evidence["trajectory"][0]["objective_revision"] == 2
    assert evidence["pending_tool_calls"] == ["call:pending"]
    assert evidence["cancelled_tool_calls"] == ["call:cancelled"]
