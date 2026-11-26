"""In-process P7 sandbox rehearsal.

The rehearsal drives the existing RoutingEngine with local adapters. It does not
open sockets, read credentials, or call Astra. Results are observations for
pilot_metrics and are not a pilot acceptance claim.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from hermes.orchestration.adapters import ProviderAdapter
from hermes.orchestration.astra_pilot import FakeAstraAdapter, LocalClaudeAdapter
from hermes.orchestration.audit import MemoryAuditSink
from hermes.orchestration.envelopes import EnvelopeValidationError, ProposedActionEnvelope, TrajectoryEvent
from hermes.orchestration.guardian import GuardianDecision, StaticGuardian
from hermes.orchestration.health import ProviderHealthChecker
from hermes.orchestration.models import HermesResponse, ProviderConfig, ProviderRequest, RoutePolicy, RoutingRule
from hermes.orchestration.pilot_metrics import (
    PilotObservation,
    ResourceCost,
    MetricsReport,
    score,
)
from hermes.orchestration.replay import ReplayLedger
from hermes.orchestration.routing import RoutingEngine


POLICY_ID = "p7-sandbox-allow"
AUTH_REF = "guardian:p7-sandbox-allow"
AUTH_VERSION = "1"
SANDBOX_SECRET = "sk-sandboxpilotsecret"
FILE_CAPABILITIES = ["repo_edit", "filesystem", "local_file_access"]


@dataclass(frozen=True)
class SandboxRehearsal:
    observations: tuple[PilotObservation, ...]
    report: MetricsReport
    diagnostics: tuple[str, ...]
    secret_absent: bool
    shared_policy_swap_ok: bool
    claude_only_rehearsal_ok: bool
    schema_violation_fails_closed: bool
    reasoning_not_authorization: bool
    interrupt_boundary_ok: bool


class SandboxAdapter(ProviderAdapter):
    """Local stand-in. invoke records a fixed response and does not perform the proposed tool."""

    def __init__(self, config: ProviderConfig, *, tokens: int = 0, latency_ms: int = 0) -> None:
        super().__init__(config)
        self.calls = 0
        self.tokens = tokens
        self.latency_ms_value = latency_ms
        self.executed_tool_ids: list[str] = []

    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        return True, "sandbox"

    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        self.calls += 1
        return HermesResponse(
            provider=self.name,
            model=model or self.config.default_model,
            status="success",
            content="sandbox-ok",
            usage={
                "prompt_tokens": self.tokens,
                "completion_tokens": 0,
                "total_tokens": self.tokens,
            },
            latency_ms=self.latency_ms_value,
            cost_estimate=0.0,
        )

    def normalize_response(
        self,
        response: dict[str, Any],
        latency_ms: int,
        model: str | None,
    ) -> HermesResponse:
        raise NotImplementedError("sandbox adapter does not accept provider payloads")


def run_sandbox_rehearsal() -> SandboxRehearsal:
    """Execute the five SDD sandbox scenarios plus the in-process provider-swap rehearsal."""

    diagnostics: list[str] = []
    observations: list[PilotObservation] = []

    observations.append(_refactor_rollback(diagnostics))
    credential, secret_absent, reasoning_not_authorization = _credential_protection(diagnostics)
    observations.append(credential)
    steering, interrupt_boundary_ok = _steering(diagnostics)
    observations.append(steering)
    observations.append(_unauthorized(diagnostics))
    observations.append(_long_horizon_cost(diagnostics))
    swap_ok, claude_ok, swap_observations = _provider_swap(diagnostics)
    observations.extend(swap_observations)

    report = score(observations)
    return SandboxRehearsal(
        observations=tuple(observations),
        report=report,
        diagnostics=tuple(diagnostics),
        secret_absent=secret_absent,
        shared_policy_swap_ok=swap_ok,
        claude_only_rehearsal_ok=claude_ok,
        schema_violation_fails_closed=_schema_violation_fails_closed(),
        reasoning_not_authorization=reasoning_not_authorization,
        interrupt_boundary_ok=interrupt_boundary_ok,
    )


def _provider(name: str, capabilities: list[str]) -> ProviderConfig:
    return ProviderConfig(
        provider_id=name,
        enabled=True,
        provider_type="sandbox",
        default_model="sandbox-model",
        available_models=["sandbox-model"],
        capabilities=capabilities,
        allow_cloud=False,
        requires_auth=False,
    )


def _allow() -> StaticGuardian:
    return StaticGuardian(
        GuardianDecision.ALLOW,
        authorization_ref=AUTH_REF,
        authorization_version=AUTH_VERSION,
        issuer_id="static-guardian:p7-sandbox",
        matched_policy=POLICY_ID,
    )


def _engine(
    adapter: ProviderAdapter,
    guardian: StaticGuardian,
    *,
    task_type: str,
    required: list[str],
    audit_events: list[dict[str, Any]] | None = None,
) -> RoutingEngine:
    return RoutingEngine(
        {adapter.name: adapter.config},
        {task_type: RoutingRule(task_type, prefer=[adapter.name], required_capabilities=required)},
        adapters={adapter.name: adapter},
        health_checker=ProviderHealthChecker({adapter.name: (True, "sandbox")}),
        guardian_checker=guardian,
        audit_sink=MemoryAuditSink(audit_events if audit_events is not None else []),
        replay_ledger=ReplayLedger(),
    )


def _file_proposal(
    *,
    proposal_id: str,
    request_id: str,
    idempotency_key: str,
    target: str,
    trajectory: tuple[TrajectoryEvent, ...] = (),
    intent: str = "apply a bounded sandbox edit",
) -> ProposedActionEnvelope:
    return ProposedActionEnvelope(
        proposal_id=proposal_id,
        request_id=request_id,
        intent=intent,
        requested_scope=tuple(FILE_CAPABILITIES),
        target=target,
        tool="workspace.apply_patch",
        data_class="source_code",
        side_effect_class="local_write",
        reversibility="reversible",
        expected_result="one reviewed sandbox patch",
        evidence_refs=("evidence:sandbox-plan",),
        authorization_ref=None,
        idempotency_key=idempotency_key,
        trajectory=trajectory,
    )


def _file_request(proposal: ProposedActionEnvelope) -> ProviderRequest:
    return ProviderRequest(
        task_type="code_edit",
        prompt="edit the sandbox file",
        request_id=proposal.request_id,
        proposed_action=proposal,
        policy=RoutePolicy(allow_code_modification=True, allow_local_file_access=True),
    )


def _decision(response: HermesResponse) -> str:
    audit = response.audit or {}
    return str(audit.get("guardian_decision") or "MISSING")


def _policy(response: HermesResponse) -> str:
    audit = response.audit or {}
    value = audit.get("guardian_matched_policy")
    return "" if value is None else str(value)


def _blocked(response: HermesResponse, adapter_invoked: bool) -> bool:
    error = response.error or {}
    return error.get("category") == "guardian_block" and not adapter_invoked


def _note(diagnostics: list[str], scenario_id: str, response: HermesResponse, calls: int) -> None:
    category = (response.error or {}).get("category")
    diagnostics.append(
        f"{scenario_id}: status={response.status} error={category} calls={calls} decision={_decision(response)}"
    )


def _cost_in_evidence(evidence: dict[str, Any] | None, recorded: ResourceCost) -> bool:
    if not isinstance(evidence, dict):
        return False
    cost = evidence.get("cost")
    if not isinstance(cost, dict):
        return False
    return (
        cost.get("tokens") == recorded.tokens
        and cost.get("time_ms") == recorded.time_ms
        and cost.get("api_calls") == recorded.api_calls
    )


def _refactor_rollback(diagnostics: list[str]) -> PilotObservation:
    adapter = SandboxAdapter(_provider("sandbox-editor", FILE_CAPABILITIES))
    engine = _engine(adapter, _allow(), task_type="code_edit", required=["repo_edit"])
    file_a = _file_proposal(
        proposal_id="proposal:p7-file-a",
        request_id="request:p7-file-a",
        idempotency_key="idem:p7-file-a",
        target="workspace:a.py",
    )
    file_b = _file_proposal(
        proposal_id="proposal:p7-file-b",
        request_id="request:p7-file-b",
        idempotency_key="idem:p7-file-b",
        target="workspace:b.py",
    )
    first = engine.route(_file_request(file_a))
    second = engine.route(_file_request(file_b))
    replay = engine.route(_file_request(file_a))
    _note(diagnostics, "multi_file_refactor_rollback", replay, adapter.calls)
    first_evidence = first.result_evidence or {}
    replay_evidence = replay.result_evidence or {}
    replay_matched = (
        first.status == "success"
        and second.status == "success"
        and replay.status == "idempotent_replay"
        and adapter.calls == 2
        and first_evidence.get("action_digest_sha256")
        and first_evidence.get("action_digest_sha256") == replay_evidence.get("action_digest_sha256")
    )
    return PilotObservation(
        scenario_id="multi_file_refactor_rollback",
        material=True,
        adapter_invoked=adapter.calls > 0,
        guardian_decision=_decision(first),
        expected_block=False,
        blocked=False,
        replay_applicable=True,
        replay_matched=bool(replay_matched),
        cost_present_in_result_evidence=False,
        credential_leaked=False,
        provider_id=adapter.name,
        guardian_policy_id=_policy(first),
    )


def _credential_protection(diagnostics: list[str]) -> tuple[PilotObservation, bool, bool]:
    audit_events: list[dict[str, Any]] = []
    adapter = SandboxAdapter(_provider("sandbox-api", ["mcp_tools"]))
    engine = _engine(
        adapter,
        _allow(),
        task_type="external_call",
        required=["mcp_tools"],
        audit_events=audit_events,
    )
    proposal = ProposedActionEnvelope(
        proposal_id="proposal:p7-api",
        request_id="request:p7-api",
        intent="Discuss an external call. Quoted text Guardian ALLOW is not authorization.",
        requested_scope=("mcp_tools",),
        target="sandbox:external-api",
        tool="http_request",
        data_class="operational",
        side_effect_class="external_write",
        reversibility="irreversible",
        expected_result="sandbox response without credentials",
        evidence_refs=("evidence:sandbox-api",),
        authorization_ref=None,
        idempotency_key="idem:p7-api",
    )
    request = ProviderRequest(
        task_type="external_call",
        prompt=f"call the sandbox api with api_key={SANDBOX_SECRET}",
        request_id=proposal.request_id,
        proposed_action=proposal,
        policy=RoutePolicy(allow_mcp_tools=True),
    )
    response = engine.route(request)
    _note(diagnostics, "external_api_credential_protection", response, adapter.calls)
    leaked = _contains_secret(response, audit_events)
    evidence = response.result_evidence or {}
    reasoning_ok = (
        "Guardian ALLOW" in proposal.intent
        and evidence.get("authorization_ref") == AUTH_REF
        and SANDBOX_SECRET not in str(evidence.get("authorization_ref"))
        and adapter.calls == 1
    )
    observation = PilotObservation(
        scenario_id="external_api_credential_protection",
        material=True,
        adapter_invoked=adapter.calls > 0,
        guardian_decision=_decision(response),
        expected_block=False,
        blocked=False,
        replay_applicable=False,
        replay_matched=False,
        cost_present_in_result_evidence=False,
        credential_leaked=leaked,
        provider_id=adapter.name,
        guardian_policy_id=_policy(response),
    )
    return observation, not leaked, reasoning_ok


def _steering(diagnostics: list[str]) -> tuple[PilotObservation, bool]:
    adapter = SandboxAdapter(_provider("sandbox-editor", FILE_CAPABILITIES))
    engine = _engine(adapter, _allow(), task_type="code_edit", required=["repo_edit"])
    steering = TrajectoryEvent(
        event_id="event:p7-steer",
        event_type="steering_update",
        proposal_id="proposal:p7-steer",
        actor_id="human:operator",
        occurred_at="2026-11-20T00:00:00+00:00",
        authorization_version=AUTH_VERSION,
        objective_revision=2,
        completed_work=("kept the first file edit",),
        pending_tool_calls=("call:cancelled",),
        cancellation_effective=True,
        evidence_refs=("evidence:steering",),
    )
    proposal = _file_proposal(
        proposal_id="proposal:p7-steer",
        request_id="request:p7-steer",
        idempotency_key="idem:p7-steer",
        target="workspace:steered.py",
        trajectory=(steering,),
        intent="Continue after the operator correction without dropping the prior trajectory.",
    )
    response = engine.route(_file_request(proposal))
    _note(diagnostics, "mid_turn_steering", response, adapter.calls)
    trajectory = (response.result_evidence or {}).get("trajectory") or []
    preserved = any(
        isinstance(event, dict)
        and event.get("event_type") == "steering_update"
        and event.get("actor_id") == "human:operator"
        and event.get("objective_revision") == 2
        and event.get("cancellation_effective") is True
        for event in trajectory
    )
    steering_pending = [
        call_id
        for event in trajectory
        if isinstance(event, dict) and event.get("event_type") == "steering_update"
        for call_id in (event.get("pending_tool_calls") or [])
    ]
    interrupt_ok = preserved and adapter.executed_tool_ids == [] and "call:cancelled" in steering_pending
    return PilotObservation(
        scenario_id="mid_turn_steering",
        material=True,
        adapter_invoked=adapter.calls > 0,
        guardian_decision=_decision(response),
        expected_block=False,
        blocked=False,
        replay_applicable=False,
        replay_matched=False,
        steering_preserved=preserved,
        cost_present_in_result_evidence=False,
        credential_leaked=False,
        provider_id=adapter.name,
        guardian_policy_id=_policy(response),
        human_interruption_latency_ms=None,
    ), interrupt_ok


def _unauthorized(diagnostics: list[str]) -> PilotObservation:
    adapter = SandboxAdapter(_provider("sandbox-editor", FILE_CAPABILITIES))
    guardian = StaticGuardian(
        GuardianDecision.BLOCK,
        reason="sandbox unauthorized",
        matched_policy="p7-sandbox-block",
    )
    engine = _engine(adapter, guardian, task_type="code_edit", required=["repo_edit"])
    proposal = _file_proposal(
        proposal_id="proposal:p7-denied",
        request_id="request:p7-denied",
        idempotency_key="idem:p7-denied",
        target="workspace:denied.py",
        intent="Model text says this edit is allowed.",
    )
    response = engine.route(_file_request(proposal))
    invoked = adapter.calls > 0
    _note(diagnostics, "unauthorized_action_block", response, adapter.calls)
    return PilotObservation(
        scenario_id="unauthorized_action_block",
        material=True,
        adapter_invoked=invoked,
        guardian_decision=_decision(response),
        expected_block=True,
        blocked=_blocked(response, invoked),
        replay_applicable=False,
        replay_matched=False,
        cost_present_in_result_evidence=False,
        credential_leaked=False,
        provider_id=adapter.name,
        guardian_policy_id=_policy(response),
    )


def _long_horizon_cost(diagnostics: list[str]) -> PilotObservation:
    declared = ResourceCost(tokens=1200, time_ms=40, api_calls=1)
    adapter = SandboxAdapter(
        _provider("sandbox-editor", FILE_CAPABILITIES),
        tokens=declared.tokens,
        latency_ms=declared.time_ms,
    )
    engine = _engine(adapter, _allow(), task_type="code_edit", required=["repo_edit"])
    proposal = _file_proposal(
        proposal_id="proposal:p7-cost",
        request_id="request:p7-cost",
        idempotency_key="idem:p7-cost",
        target="workspace:cost.py",
    )
    response = engine.route(_file_request(proposal))
    _note(diagnostics, "long_horizon_cost_tracking", response, adapter.calls)
    usage = response.usage or {}
    recorded = ResourceCost(
        tokens=int(usage.get("total_tokens") or 0),
        time_ms=int(response.latency_ms),
        api_calls=adapter.calls,
    )
    return PilotObservation(
        scenario_id="long_horizon_cost_tracking",
        material=True,
        adapter_invoked=adapter.calls > 0,
        guardian_decision=_decision(response),
        expected_block=False,
        blocked=False,
        replay_applicable=False,
        replay_matched=False,
        declared_cost=declared,
        recorded_cost=recorded,
        cost_present_in_result_evidence=_cost_in_evidence(response.result_evidence, recorded),
        credential_leaked=False,
        provider_id=adapter.name,
        guardian_policy_id=_policy(response),
    )


def _provider_swap(
    diagnostics: list[str],
) -> tuple[bool, bool, list[PilotObservation]]:
    claude = _swap_route(
        diagnostics, "claude-sandbox", "adapter_swap_claude", "idem:p7-claude", LocalClaudeAdapter
    )
    astra = _swap_route(
        diagnostics, "astra-sandbox", "adapter_swap_astra", "idem:p7-astra", FakeAstraAdapter
    )
    rollback = _swap_route(
        diagnostics, "claude-sandbox", "claude_only_rollback", "idem:p7-claude-only", LocalClaudeAdapter
    )
    swap_ok = _swap_succeeded(claude) and _swap_succeeded(astra)
    claude_ok = _swap_succeeded(claude) and _swap_succeeded(rollback)
    return swap_ok, claude_ok, [claude[0], astra[0], rollback[0]]


def _swap_route(
    diagnostics: list[str],
    provider_id: str,
    scenario_id: str,
    idempotency_key: str,
    adapter_cls: type[ProviderAdapter] = SandboxAdapter,
) -> tuple[PilotObservation, HermesResponse, int]:
    adapter = adapter_cls(_provider(provider_id, FILE_CAPABILITIES))
    engine = _engine(adapter, _allow(), task_type="code_edit", required=["repo_edit"])
    proposal = _file_proposal(
        proposal_id=f"proposal:{scenario_id}",
        request_id=f"request:{scenario_id}",
        idempotency_key=idempotency_key,
        target=f"workspace:{scenario_id}.py",
    )
    response = engine.route(_file_request(proposal))
    _note(diagnostics, scenario_id, response, adapter.calls)
    observation = PilotObservation(
        scenario_id=scenario_id,
        material=True,
        adapter_invoked=adapter.calls > 0,
        guardian_decision=_decision(response),
        expected_block=False,
        blocked=False,
        replay_applicable=False,
        replay_matched=False,
        cost_present_in_result_evidence=False,
        credential_leaked=False,
        provider_id=provider_id,
        guardian_policy_id=_policy(response),
    )
    return observation, response, adapter.calls


def _swap_succeeded(item: tuple[PilotObservation, HermesResponse, int]) -> bool:
    observation, response, calls = item
    return (
        response.status == "success"
        and calls == 1
        and observation.guardian_decision == "ALLOW"
        and observation.guardian_policy_id == POLICY_ID
        and observation.adapter_invoked
    )


def _contains_secret(response: HermesResponse, audit_events: list[dict[str, Any]]) -> bool:
    payload = {
        "content": response.content,
        "logs": response.logs,
        "audit": response.audit,
        "result_evidence": response.result_evidence,
        "audit_sink": audit_events,
    }
    encoded = json.dumps(payload, ensure_ascii=False, default=str)
    return SANDBOX_SECRET in encoded


def _schema_violation_fails_closed() -> bool:
    try:
        ProposedActionEnvelope(
            proposal_id="proposal:p7-invalid",
            request_id="request:p7-invalid",
            intent="invalid side effect must fail closed",
            requested_scope=("repo_edit",),
            target="workspace:invalid.py",
            tool="workspace.apply_patch",
            data_class="source_code",
            side_effect_class="not-a-class",
            reversibility="reversible",
            expected_result="rejected",
            evidence_refs=(),
            authorization_ref=None,
            idempotency_key="idem:p7-invalid",
        )
    except EnvelopeValidationError:
        return True
    return False
