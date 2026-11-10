"""Routing engine and fallback handling for Hermes providers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from hermes.orchestration.audit import AuditSink, NoopAuditSink, timestamp_now
from hermes.orchestration.adapters import ProviderAdapter, adapter_for
from hermes.orchestration.config_loader import split_provider_ref
from hermes.orchestration.guardian import (
    DANGEROUS_CAPABILITIES,
    FailClosedGuardian,
    GuardianChecker,
    GuardianDecision,
    GuardianResult,
    NoopPlanningGuardian,
)
from hermes.orchestration.health import ProviderHealthChecker
from hermes.orchestration.models import COST_TIERS, HermesResponse, ProviderConfig, ProviderRequest, RoutingRule


TOOL_EXPOSURE_CAPABILITIES = {
    "terminal",
    "filesystem",
    "local_file_access",
    "repo_edit",
    "mcp_tools",
    "test_runner",
    "local_sensitive",
}

KNOWN_TOOL_CAPABILITIES = {
    *TOOL_EXPOSURE_CAPABILITIES,
    "codebase_context",
    "general_reasoning",
    "codebase_analysis",
    "architecture_design",
    "long_context",
    "creative_generation",
    "fast_answer",
    "cheap_batch",
    "refactor",
    "diff_generation",
    "long_reasoning",
    "writing",
    "architecture_review",
}


@dataclass(frozen=True)
class Candidate:
    provider_id: str
    model: str | None
    reason: str


class RoutingEngine:
    """Selects providers, invokes adapters, and records fallback reasons."""

    def __init__(
        self,
        providers: dict[str, ProviderConfig],
        routing_rules: dict[str, RoutingRule],
        adapters: dict[str, ProviderAdapter] | None = None,
        health_checker: ProviderHealthChecker | None = None,
        guardian_checker: GuardianChecker | None = None,
        audit_sink: AuditSink | None = None,
    ):
        self.providers = providers
        self.routing_rules = routing_rules
        self.adapters = adapters or {pid: adapter_for(config) for pid, config in providers.items()}
        self.health_checker = health_checker or ProviderHealthChecker()
        self.guardian_checker = guardian_checker
        self.audit_sink = audit_sink or NoopAuditSink()

    def select(self, request: ProviderRequest) -> tuple[Candidate | None, list[str]]:
        """Return the best eligible candidate and decision logs."""

        logs: list[str] = []
        preferred_error = self._preferred_provider_error(request)
        if preferred_error:
            _category, message = preferred_error
            return None, [message]
        capability_error = self._capability_error(request)
        if capability_error:
            _category, message = capability_error
            return None, [message]
        for index, candidate in enumerate(self.candidates(request)):
            provider = self.providers[candidate.provider_id]
            ok, reason = self._eligible(provider, request)
            if not ok:
                logs.append(f"skip {provider.provider_id}: {reason}")
                locked = self._locked_selection_log(request, candidate, index)
                if locked:
                    logs.append(locked)
                    return None, logs
                continue
            model_ok, _selected_model, model_reason = self._model_for(provider, candidate.model)
            if not model_ok:
                logs.append(f"skip {provider.provider_id}: {model_reason}")
                locked = self._locked_selection_log(request, candidate, index)
                if locked:
                    logs.append(locked)
                    return None, logs
                continue
            healthy, health_reason = self.health_checker.check(self.adapters[provider.provider_id])
            if not healthy:
                logs.append(f"skip {provider.provider_id}: health_check failed ({health_reason})")
                locked = self._locked_selection_log(request, candidate, index)
                if locked:
                    logs.append(locked)
                    return None, logs
                continue
            logs.append(f"selected {provider.provider_id}: {candidate.reason}")
            return candidate, logs
        logs.append("no eligible provider found")
        return None, logs

    def candidates(self, request: ProviderRequest) -> list[Candidate]:
        """Build an ordered candidate list from policy, rule, fallbacks, and priorities."""

        rule = self.routing_rules.get(request.task_type)
        ordered_refs: list[str] = []
        if request.policy.preferred_provider:
            ordered_refs.append(request.policy.preferred_provider)
        if rule:
            ordered_refs.extend(rule.prefer)
            ordered_refs.extend(rule.fallback_order)

        for provider in sorted(self.providers.values(), key=lambda p: (p.priority, p.provider_id)):
            if provider.provider_id not in ordered_refs:
                ordered_refs.append(provider.provider_id)
            if provider.fallback_provider and provider.fallback_provider not in ordered_refs:
                ordered_refs.append(provider.fallback_provider)

        seen: set[tuple[str, str | None]] = set()
        candidates: list[Candidate] = []
        for ref in ordered_refs:
            provider_id, model = split_provider_ref(ref, self.providers)
            if provider_id not in self.providers:
                continue
            key = (provider_id, model)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(Candidate(provider_id=provider_id, model=model, reason=f"matched route ref {ref}"))
        return candidates

    def route(self, request: ProviderRequest, dry_run: bool = False, check_health: bool = False) -> HermesResponse:
        """Route and optionally invoke a provider with fallback."""

        attempts: list[dict[str, Any]] = []
        logs: list[str] = []
        health_checked = False
        preferred_error = self._preferred_provider_error(request)
        if preferred_error:
            error_category, error_message = preferred_error
            audit = self._audit_event(
                request=request,
                provider="none",
                model=None,
                status="error",
                attempts=attempts,
                health_checked=health_checked,
                guardian_result=GuardianResult(GuardianDecision.NOT_CHECKED, "route rejected before selection"),
                dry_run=dry_run,
                error_category=error_category,
            )
            response = HermesResponse(
                provider="none",
                model=None,
                status="error",
                content=error_message,
                logs=[error_message],
                error={"category": error_category, "message": error_message},
                dry_run=dry_run,
                health_checked=health_checked,
                audit=audit,
            )
            self._emit_audit(audit)
            return response
        capability_error = self._capability_error(request)
        if capability_error:
            error_category, error_message = capability_error
            audit = self._audit_event(
                request=request,
                provider="none",
                model=None,
                status="error",
                attempts=attempts,
                health_checked=health_checked,
                guardian_result=GuardianResult(GuardianDecision.NOT_CHECKED, "route rejected before selection"),
                dry_run=dry_run,
                error_category=error_category,
            )
            response = HermesResponse(
                provider="none",
                model=None,
                status="error",
                content=error_message,
                logs=[error_message],
                error={"category": error_category, "message": error_message},
                dry_run=dry_run,
                health_checked=health_checked,
                audit=audit,
            )
            self._emit_audit(audit)
            return response
        for index, candidate in enumerate(self.candidates(request)):
            provider = self.providers[candidate.provider_id]
            ok, reason = self._eligible(provider, request)
            if not ok:
                logs.append(f"skip {provider.provider_id}: {reason}")
                attempts.append({"provider": provider.provider_id, "status": "skipped", "reason": reason})
                locked = self._locked_fallback_error(request, candidate, index, attempts, logs, health_checked, dry_run)
                if locked:
                    return locked
                continue
            model_ok, selected_model, model_reason = self._model_for(provider, candidate.model)
            if not model_ok:
                attempts.append({"provider": provider.provider_id, "status": "skipped", "reason": model_reason})
                logs.append(f"skip {provider.provider_id}: {model_reason}")
                locked = self._locked_fallback_error(request, candidate, index, attempts, logs, health_checked, dry_run)
                if locked:
                    return locked
                continue

            guardian_result = self._guardian_result(request, provider, dry_run=dry_run)
            guardian_error = self._guardian_error(request, provider, guardian_result, dry_run=dry_run)
            if guardian_error:
                status, error_category = guardian_error
                audit = self._audit_event(
                    request=request,
                    provider=provider.provider_id,
                    model=selected_model,
                    status=status,
                    attempts=attempts,
                    health_checked=health_checked,
                    guardian_result=guardian_result,
                    dry_run=dry_run,
                    error_category=error_category,
                )
                response = HermesResponse(
                    provider="none",
                    model=None,
                    status="error",
                    content=guardian_result.reason or f"Guardian decision: {_decision_value(guardian_result.decision)}",
                    logs=[*logs, f"guardian_decision: {_decision_value(guardian_result.decision)}"],
                    fallback={"attempts": attempts} if attempts else None,
                    error={"category": error_category, "message": guardian_result.reason},
                    audit=audit,
                    dry_run=dry_run,
                    health_checked=health_checked,
                )
                self._emit_audit(audit)
                return response

            if dry_run and not check_health:
                healthy, health_reason = True, "dry-run: health not checked"
            else:
                health_checked = True
                healthy, health_reason = self.health_checker.check(self.adapters[provider.provider_id])
                if not healthy:
                    attempts.append({"provider": provider.provider_id, "status": "unhealthy", "reason": health_reason})
                    logs.append(f"skip {provider.provider_id}: health_check failed ({health_reason})")
                    locked = self._locked_fallback_error(
                        request,
                        candidate,
                        index,
                        attempts,
                        logs,
                        health_checked,
                        dry_run,
                    )
                    if locked:
                        return locked
                    continue

            if dry_run:
                audit = self._audit_event(
                    request=request,
                    provider=provider.provider_id,
                    model=selected_model,
                    status="success",
                    attempts=attempts,
                    health_checked=health_checked,
                    guardian_result=guardian_result,
                    dry_run=True,
                )
                self._emit_audit(audit)
                return HermesResponse(
                    provider=provider.provider_id,
                    model=selected_model,
                    status="success",
                    content=f"Dry run selected provider: {provider.provider_id}",
                    logs=[
                        *logs,
                        "dry_run: true",
                        f"health_checked: {str(health_checked).lower()}",
                        f"guardian_checked: {str(audit['guardian_checked']).lower()}",
                        f"guardian_decision: {audit['guardian_decision']}",
                        (
                            "provider availability was verified"
                            if health_checked
                            else "provider availability was not verified"
                        ),
                        f"selected {provider.provider_id}: {candidate.reason}",
                    ],
                    fallback={
                        "attempts": attempts,
                        "planned_fallback_provider": (
                            provider.fallback_provider
                            if provider.fallback_provider in self.providers
                            else None
                        ),
                    },
                    audit=audit,
                    dry_run=True,
                    health_checked=health_checked,
                )

            response = self.adapters[provider.provider_id].invoke(request, selected_model)
            response.logs = [*logs, *response.logs]
            if response.status == "success":
                if attempts:
                    response.status = "fallback"
                    response.fallback = {
                        "attempts": attempts,
                        "fallback_provider_used": provider.provider_id,
                    }
                response.dry_run = False
                response.health_checked = True
                response.audit = self._audit_event(
                    request=request,
                    provider=provider.provider_id,
                    model=selected_model,
                    status=response.status,
                    attempts=attempts,
                    health_checked=health_checked,
                    guardian_result=guardian_result,
                    dry_run=False,
                )
                self._emit_audit(response.audit)
                return response

            attempts.append(
                {
                    "provider": provider.provider_id,
                    "status": "error",
                    "reason": "; ".join(response.logs) or response.content or "provider returned error",
                }
            )
            logs.append(f"provider {provider.provider_id} failed; trying fallback")
            locked = self._locked_fallback_error(request, candidate, index, attempts, logs, health_checked, dry_run)
            if locked:
                return locked

        audit = self._audit_event(
            request=request,
            provider="none",
            model=None,
            status="error",
            attempts=attempts,
            health_checked=health_checked,
            guardian_result=GuardianResult(GuardianDecision.NOT_CHECKED, "no selected dangerous route"),
            dry_run=dry_run,
            error_category="no_eligible_provider",
        )
        response = HermesResponse(
            provider="none",
            model=None,
            status="error",
            content="No eligible provider could satisfy the request.",
            logs=logs,
            fallback={"attempts": attempts} if attempts else None,
            error={"category": "no_eligible_provider", "message": "No eligible provider could satisfy the request."},
            dry_run=dry_run,
            health_checked=health_checked,
            audit=audit,
        )
        self._emit_audit(audit)
        return response

    def _eligible(self, provider: ProviderConfig, request: ProviderRequest) -> tuple[bool, str]:
        rule = self.routing_rules.get(request.task_type)
        policy = request.policy.with_rule_defaults(rule)
        required = self._requested_capabilities(request)
        tool_capabilities = self._tool_capabilities(request.tools)

        if not provider.enabled:
            return False, "provider disabled"
        if not policy.allow_cloud and provider.allow_cloud:
            return False, "cloud providers disallowed by policy"
        if COST_TIERS[provider.cost_tier] > COST_TIERS[policy.max_cost_tier]:
            return False, f"cost tier {provider.cost_tier} exceeds policy {policy.max_cost_tier}"
        if not provider.supports_capabilities(required):
            missing = sorted(required.difference(provider.capabilities))
            return False, f"missing capabilities: {', '.join(missing)}"
        if {"local_file_access", "filesystem"} & required and not policy.allow_local_file_access:
            return False, "local file access disallowed by policy"
        if "repo_edit" in required and not policy.allow_code_modification:
            return False, "code modification disallowed by policy"
        if {"terminal", "test_runner"} & required and not policy.allow_terminal_execution:
            return False, "terminal execution disallowed by policy"
        if "mcp_tools" in required and not policy.allow_mcp_tools:
            return False, "MCP tool exposure disallowed by policy"
        if tool_capabilities and not provider.supports_capabilities(tool_capabilities):
            missing = sorted(tool_capabilities.difference(provider.capabilities))
            return False, f"missing tool capabilities: {', '.join(missing)}"
        if {"terminal", "test_runner"} & tool_capabilities and not policy.allow_terminal_execution:
            return False, "terminal tool exposure disallowed by policy"
        if "mcp_tools" in tool_capabilities and not policy.allow_mcp_tools:
            return False, "MCP tool exposure disallowed by policy"
        if {"filesystem", "local_file_access"} & tool_capabilities and not policy.allow_local_file_access:
            return False, "local file access tool exposure disallowed by policy"
        if "repo_edit" in tool_capabilities and not policy.allow_code_modification:
            return False, "code modification tool exposure disallowed by policy"
        return True, "eligible"

    def _effective_policy(self, request: ProviderRequest) -> dict[str, Any]:
        rule = self.routing_rules.get(request.task_type)
        return request.policy.with_rule_defaults(rule).to_dict()

    def _audit_event(
        self,
        *,
        request: ProviderRequest,
        provider: str,
        model: str | None,
        status: str,
        attempts: list[dict[str, Any]],
        health_checked: bool,
        guardian_result: GuardianResult,
        dry_run: bool,
        error_category: str | None = None,
    ) -> dict[str, Any]:
        rule = self.routing_rules.get(request.task_type)
        try:
            required = self._requested_capabilities(request)
        except ValueError:
            required = set(request.required_capabilities)
            if rule:
                required.update(rule.required_capabilities)
        event = {
            "timestamp": timestamp_now(),
            "selected_provider": provider,
            "selected_model": model,
            "task_type": request.task_type,
            "requested_capabilities": sorted(required),
            "effective_policy": self._effective_policy(request),
            "guardian_checked": _decision_value(guardian_result.decision) != GuardianDecision.NOT_CHECKED.value,
            "guardian_decision": _decision_value(guardian_result.decision),
            "guardian_reason": guardian_result.reason,
            "guardian_matched_policy": guardian_result.matched_policy,
            "health_checked": health_checked,
            "dry_run": dry_run,
            "fallback_attempts": attempts,
            "invocation_status": status,
        }
        if error_category:
            event["error_category"] = error_category
        return event

    def _dangerous_capabilities(self, request: ProviderRequest, provider: ProviderConfig) -> set[str]:
        requested = self._requested_capabilities(request)
        return set(provider.capabilities).intersection(DANGEROUS_CAPABILITIES).intersection(requested)

    def _guardian_result(self, request: ProviderRequest, provider: ProviderConfig, *, dry_run: bool) -> GuardianResult:
        dangerous = self._dangerous_capabilities(request, provider)
        if not dangerous:
            return GuardianResult(GuardianDecision.NOT_CHECKED, "no dangerous capabilities requested")
        checker = self.guardian_checker
        if checker is None:
            checker = NoopPlanningGuardian() if dry_run else FailClosedGuardian()
        return checker.check(request=request, provider=provider, capabilities=dangerous, dry_run=dry_run)

    def _guardian_error(
        self,
        request: ProviderRequest,
        provider: ProviderConfig,
        guardian_result: GuardianResult,
        *,
        dry_run: bool,
    ) -> tuple[str, str] | None:
        decision = _decision_value(guardian_result.decision)
        if decision == GuardianDecision.BLOCK.value:
            return "blocked", "guardian_block"
        if decision == GuardianDecision.REVIEW_REQUIRED.value:
            return "review_required", "guardian_review_required"
        if dry_run or not self._dangerous_capabilities(request, provider):
            return None
        if decision == GuardianDecision.ALLOW.value:
            return None
        if decision == GuardianDecision.NOT_CHECKED.value:
            return "blocked", "guardian_not_checked"
        return "blocked", "guardian_not_allowed"

    def _emit_audit(self, audit: dict[str, Any]) -> None:
        self.audit_sink.emit(audit)

    def _preferred_provider_error(self, request: ProviderRequest) -> tuple[str, str] | None:
        ref = request.policy.preferred_provider
        if not ref:
            return None
        provider_id, model = split_provider_ref(ref, self.providers)
        provider = self.providers.get(provider_id)
        if provider is None:
            return "invalid_provider_reference", f"unknown provider reference {ref!r}"
        if model is None:
            return None
        ok, _selected, reason = self._model_for(provider, model)
        if ok:
            return None
        return "invalid_model_reference", reason

    def _requested_capabilities(self, request: ProviderRequest) -> set[str]:
        rule = self.routing_rules.get(request.task_type)
        required = set(request.required_capabilities)
        if rule:
            required.update(rule.required_capabilities)
        required.update(self._tool_capabilities(request.tools))
        return required

    @staticmethod
    def _model_for(provider: ProviderConfig, model_alias: str | None) -> tuple[bool, str | None, str]:
        if model_alias and model_alias in provider.metadata.get("model_aliases", {}):
            return True, provider.metadata["model_aliases"][model_alias], "resolved model alias"
        if model_alias and model_alias in provider.available_models:
            return True, model_alias, "resolved direct model"
        if model_alias:
            return False, None, f"unknown model alias or model {model_alias!r} for provider {provider.provider_id!r}"
        return True, provider.default_model, "using default model"

    @staticmethod
    def _tool_capabilities(tools: list[dict[str, Any]] | None) -> set[str]:
        return classify_tools(tools)

    def _capability_error(self, request: ProviderRequest) -> tuple[str, str] | None:
        try:
            self._requested_capabilities(request)
        except ValueError as exc:
            return "invalid_tool_capability", str(exc)
        return None

    def _locked_fallback_error(
        self,
        request: ProviderRequest,
        candidate: Candidate,
        index: int,
        attempts: list[dict[str, Any]],
        logs: list[str],
        health_checked: bool,
        dry_run: bool,
    ) -> HermesResponse | None:
        category: str | None = None
        message: str | None = None
        if request.policy.require_preferred_provider and self._is_preferred_candidate(request, candidate):
            category = "preferred_provider_unavailable"
            message = f"preferred provider {request.policy.preferred_provider!r} was unavailable; fallback disabled"
        elif request.policy.no_fallback and index == 0:
            category = "fallback_disabled"
            message = "first route candidate failed and no_fallback is enabled"
        if not category or not message:
            return None
        audit = self._audit_event(
            request=request,
            provider="none",
            model=None,
            status="error",
            attempts=attempts,
            health_checked=health_checked,
            guardian_result=GuardianResult(GuardianDecision.NOT_CHECKED, message),
            dry_run=dry_run,
            error_category=category,
        )
        response = HermesResponse(
            provider="none",
            model=None,
            status="error",
            content=message,
            logs=[*logs, message],
            fallback={"attempts": attempts} if attempts else None,
            error={"category": category, "message": message},
            dry_run=dry_run,
            health_checked=health_checked,
            audit=audit,
        )
        self._emit_audit(audit)
        return response

    def _locked_selection_log(self, request: ProviderRequest, candidate: Candidate, index: int) -> str | None:
        if request.policy.require_preferred_provider and self._is_preferred_candidate(request, candidate):
            return f"preferred provider {request.policy.preferred_provider!r} was unavailable; fallback disabled"
        if request.policy.no_fallback and index == 0:
            return "first route candidate failed and no_fallback is enabled"
        return None

    def _is_preferred_candidate(self, request: ProviderRequest, candidate: Candidate) -> bool:
        ref = request.policy.preferred_provider
        if not ref:
            return False
        provider_id, model = split_provider_ref(ref, self.providers)
        return candidate.provider_id == provider_id and candidate.model == model


def classify_tools(tools: list[dict[str, Any]] | None) -> set[str]:
    """Classify exposed tools into required Hermes capabilities."""

    if not tools:
        return set()
    capabilities: set[str] = set()
    for tool in tools:
        capabilities.update(_explicit_tool_capabilities(tool))
        tokens = _tool_tokens(tool)
        if tokens & {"run", "execute", "bash", "shell", "terminal", "exec", "command", "subprocess", "process", "powershell", "pwsh", "python", "python_exec", "node", "npm", "npx"}:
            capabilities.add("terminal")
        if tokens & {"readfile", "read_file", "read", "file", "filesystem", "fs", "glob", "read_path", "path", "directory", "dir", "upload", "download"}:
            capabilities.update({"filesystem", "local_file_access"})
        if tokens & {
            "writefile",
            "write_file",
            "writetext",
            "write_text",
            "write",
            "delete",
            "patch",
            "save",
            "create",
            "modify",
            "update_file",
            "rm",
            "remove",
            "unlink",
            "move",
            "rename",
        }:
            capabilities.update({"repo_edit", "filesystem", "local_file_access"})
        if tokens & {
            "mcp",
            "browser",
            "send_message",
            "http_request",
            "httprequest",
            "httpclient",
            "fetch",
            "network",
            "request",
            "url",
            "open_url",
            "openurl",
            "urlopen",
        }:
            capabilities.add("mcp_tools")
    return capabilities


def _explicit_tool_capabilities(tool: dict[str, Any]) -> set[str]:
    raw_values = [
        tool.get("capabilities"),
        tool.get("x-hermes-capabilities"),
        (tool.get("function") or {}).get("x-hermes-capabilities") if isinstance(tool.get("function"), dict) else None,
        (tool.get("metadata") or {}).get("capabilities") if isinstance(tool.get("metadata"), dict) else None,
    ]
    capabilities: set[str] = set()
    for raw in raw_values:
        if raw is None:
            continue
        if isinstance(raw, str):
            values = [raw]
        elif isinstance(raw, list):
            values = raw
        else:
            raise ValueError("tool explicit capabilities must be a string or list")
        for value in values:
            capability = str(value)
            if capability not in KNOWN_TOOL_CAPABILITIES:
                raise ValueError(f"unknown explicit tool capability {capability!r}")
            if capability not in TOOL_EXPOSURE_CAPABILITIES:
                raise ValueError(
                    f"explicit tool capability {capability!r} is a provider/task capability, not a tool exposure capability"
                )
            capabilities.add(capability)
    return capabilities


def _decision_value(decision: GuardianDecision | str) -> str:
    if isinstance(decision, GuardianDecision):
        return decision.value
    return str(decision)


def _walk_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(_walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return values
    return [value]


def _tool_tokens(tool: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for value in _walk_values(tool):
        compact = re.sub(r"[^A-Za-z0-9]+", "", str(value)).lower()
        if compact:
            tokens.add(compact)
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value))
        text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
        for token in re.findall(r"[a-z0-9_]+", text.lower()):
            tokens.add(token)
            tokens.update(part for part in token.split("_") if part)
    return tokens
