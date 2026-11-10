from __future__ import annotations

from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import threading
from typing import Any

import pytest

from hermes.orchestration.audit import JsonlAuditSink, MemoryAuditSink
from hermes.orchestration.adapters import OpenAICompatibleAdapter, ProviderAdapter
from hermes.orchestration.config_loader import (
    ConfigError,
    load_orchestration_config,
    load_provider_registry,
    load_routing_rules,
    validate_route_consistency,
    validate_task_safety,
)
from hermes.orchestration.guardian import GuardianDecision, StaticGuardian
from hermes.orchestration.health import ProviderHealthChecker
from hermes.orchestration.models import HermesResponse, ProviderConfig, ProviderRequest, RoutePolicy, RoutingRule
from hermes.orchestration.routing import RoutingEngine, classify_tools


ROOT = Path(__file__).resolve().parents[1]


class FakeAdapter(ProviderAdapter):
    def __init__(self, config: ProviderConfig, status: str = "success"):
        super().__init__(config)
        self.status = status
        self.invoked = False

    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        return True, "fake healthy"

    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        self.invoked = True
        return HermesResponse(
            provider=self.name,
            model=model or self.config.default_model,
            status=self.status,
            content=f"{self.name}:{self.status}",
        )

    def normalize_response(self, response: dict[str, Any], latency_ms: int, model: str | None) -> HermesResponse:
        return HermesResponse(provider=self.name, model=model, status="success", content="")


def provider(
    provider_id: str,
    capabilities: list[str],
    *,
    enabled: bool = True,
    allow_cloud: bool = True,
    cost_tier: str = "medium",
    priority: int = 10,
    api_key_env: str | None = None,
    requires_auth: bool = True,
    base_url: str | None = None,
    local_trust_boundary: str = "private_network",
    metadata: dict[str, Any] | None = None,
) -> ProviderConfig:
    return ProviderConfig(
        provider_id=provider_id,
        enabled=enabled,
        provider_type="openai-compatible",
        base_url=base_url or f"http://localhost/{provider_id}/v1",
        api_key_env=api_key_env,
        default_model=f"{provider_id}/model",
        available_models=[f"{provider_id}/model"],
        capabilities=capabilities,
        priority=priority,
        cost_tier=cost_tier,
        allow_cloud=allow_cloud,
        local_trust_boundary=local_trust_boundary,
        requires_auth=requires_auth,
        metadata=metadata or {},
    )


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, Any], status: int = 200):
        self.payload = payload
        self.status = status

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_load_default_configs() -> None:
    providers, rules = load_orchestration_config(
        ROOT / "config" / "provider_registry.yaml",
        ROOT / "config" / "routing_rules.yaml",
    )
    assert "copilot" in providers
    assert "openrouter" in providers
    assert "cursor_worker" in providers
    assert "code_edit" in rules


def test_default_config_has_no_impossible_preferred_routes() -> None:
    providers, rules = load_orchestration_config(
        ROOT / "config" / "provider_registry.yaml",
        ROOT / "config" / "routing_rules.yaml",
    )
    assert validate_route_consistency(providers, rules) == []


def test_current_config_has_no_task_safety_issues() -> None:
    _providers, rules = load_orchestration_config(
        ROOT / "config" / "provider_registry.yaml",
        ROOT / "config" / "routing_rules.yaml",
    )
    assert validate_task_safety(rules) == []


def test_task_safety_lints_code_edit_without_repo_edit_or_file_access() -> None:
    issues = validate_task_safety({"code_edit": RoutingRule("code_edit", required_capabilities=["general_reasoning"])})
    assert issues
    assert "repo_edit" in issues[0]


def test_task_safety_lints_test_runner_without_test_or_terminal_capability() -> None:
    issues = validate_task_safety({"test_runner": RoutingRule("test_runner", required_capabilities=["general_reasoning"])})
    assert issues
    assert "test_runner or terminal" in issues[0]


def test_task_safety_lints_terminal_task_without_terminal() -> None:
    issues = validate_task_safety({"run_command": RoutingRule("run_command", required_capabilities=["general_reasoning"])})
    assert issues
    assert "terminal" in issues[0]


def test_provider_selection_prefers_rule_order() -> None:
    providers = {
        "cursor_worker": provider("cursor_worker", ["repo_edit", "local_file_access"], allow_cloud=False),
        "copilot": provider("copilot", ["repo_edit", "local_file_access"]),
    }
    rules = {
        "code_edit": RoutingRule(
            task_type="code_edit",
            prefer=["cursor_worker", "copilot"],
            required_capabilities=["repo_edit", "local_file_access"],
        )
    }
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({pid: (True, "ok") for pid in providers}),
    )
    request = ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
    )
    result = engine.route(request, dry_run=True)
    assert result.provider == "cursor_worker"


def test_code_edit_without_explicit_edit_permission_selects_no_repo_editor() -> None:
    providers = {
        "cursor_worker": provider("cursor_worker", ["repo_edit", "local_file_access"], allow_cloud=False),
        "codex_cli_worker": provider("codex_cli_worker", ["repo_edit", "local_file_access"], allow_cloud=False),
    }
    rules = {
        "code_edit": RoutingRule(
            "code_edit",
            prefer=["cursor_worker", "codex_cli_worker"],
            required_capabilities=["repo_edit", "local_file_access"],
            allow_local_file_access=True,
            allow_code_modification=True,
        )
    }
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({pid: (True, "ok") for pid in providers}),
    )
    result = engine.route(ProviderRequest(task_type="code_edit", prompt="edit"), dry_run=True)
    assert result.provider == "none"
    assert any(
        "code modification disallowed" in log or "local file access disallowed" in log
        for log in result.logs
    )


def test_test_runner_without_terminal_permission_selects_no_terminal_provider() -> None:
    providers = {
        "vscode_worker": provider("vscode_worker", ["test_runner", "terminal", "local_file_access"], allow_cloud=False),
        "codex_cli_worker": provider("codex_cli_worker", ["test_runner", "terminal", "local_file_access"], allow_cloud=False),
    }
    rules = {
        "test_runner": RoutingRule(
            "test_runner",
            prefer=["vscode_worker", "codex_cli_worker"],
            required_capabilities=["test_runner"],
            allow_cloud=False,
            allow_local_file_access=True,
            allow_terminal_execution=True,
        )
    }
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({pid: (True, "ok") for pid in providers}),
    )
    request = ProviderRequest(
        task_type="test_runner",
        prompt="test",
        policy=RoutePolicy(allow_local_file_access=True),
    )
    result = engine.route(request, dry_run=True)
    assert result.provider == "none"
    assert any("terminal execution disallowed" in log for log in result.logs)


def test_test_runner_requires_execution_permission_without_terminal_provider_capability() -> None:
    providers = {"runner": provider("runner", ["test_runner", "local_file_access"], allow_cloud=False)}
    rules = {
        "test_runner": RoutingRule(
            "test_runner",
            prefer=["runner"],
            required_capabilities=["test_runner"],
            allow_cloud=False,
            allow_local_file_access=True,
            allow_terminal_execution=True,
        )
    }
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"runner": FakeAdapter(providers["runner"])},
        health_checker=ProviderHealthChecker({"runner": (True, "ok")}),
    )
    denied = engine.route(
        ProviderRequest(
            task_type="test_runner",
            prompt="test",
            policy=RoutePolicy(allow_local_file_access=True),
        ),
        dry_run=True,
    )
    assert denied.provider == "none"
    assert any("terminal execution disallowed" in log for log in denied.logs)

    allowed = engine.route(
        ProviderRequest(
            task_type="test_runner",
            prompt="test",
            policy=RoutePolicy(allow_local_file_access=True, allow_terminal_execution=True),
        ),
        dry_run=True,
    )
    assert allowed.provider == "runner"


def test_explicit_terminal_permission_allows_test_runner_route() -> None:
    providers = {
        "vscode_worker": provider("vscode_worker", ["test_runner", "terminal", "local_file_access"], allow_cloud=False),
    }
    rules = {
        "test_runner": RoutingRule(
            "test_runner",
            prefer=["vscode_worker"],
            required_capabilities=["test_runner"],
            allow_cloud=False,
            allow_local_file_access=True,
            allow_terminal_execution=True,
        )
    }
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"vscode_worker": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="test_runner",
        prompt="test",
        policy=RoutePolicy(allow_local_file_access=True, allow_terminal_execution=True),
    )
    result = engine.route(request, dry_run=True)
    assert result.provider == "vscode_worker"


def test_test_runner_live_requires_guardian_allow() -> None:
    providers = {
        "vscode_worker": provider("vscode_worker", ["test_runner", "terminal", "local_file_access"], allow_cloud=False),
    }
    rules = {
        "test_runner": RoutingRule(
            "test_runner",
            prefer=["vscode_worker"],
            required_capabilities=["test_runner", "terminal"],
            allow_cloud=False,
            allow_local_file_access=True,
            allow_terminal_execution=True,
        )
    }
    adapter = FakeAdapter(providers["vscode_worker"])
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"vscode_worker": adapter},
        health_checker=ProviderHealthChecker({"vscode_worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.NOT_CHECKED, reason="not checked"),
    )
    request = ProviderRequest(
        task_type="test_runner",
        prompt="test",
        policy=RoutePolicy(allow_local_file_access=True, allow_terminal_execution=True),
    )
    result = engine.route(request, dry_run=False)
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "guardian_not_checked"
    assert adapter.invoked is False


def test_unavailable_provider_fallback() -> None:
    providers = {
        "primary": provider("primary", ["general_reasoning"]),
        "fallback": provider("fallback", ["general_reasoning"]),
    }
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["primary", "fallback"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"primary": (False, "down"), "fallback": (True, "ok")}),
    )
    result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=True, check_health=True)
    assert result.provider == "fallback"
    assert result.fallback is not None
    assert result.fallback["attempts"][0]["provider"] == "primary"


def test_provider_error_invocation_falls_back_to_next_provider() -> None:
    providers = {
        "primary": provider("primary", ["general_reasoning"]),
        "fallback": provider("fallback", ["general_reasoning"]),
    }
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["primary", "fallback"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"primary": FakeAdapter(providers["primary"], "error"), "fallback": FakeAdapter(providers["fallback"])},
        health_checker=ProviderHealthChecker({"primary": (True, "ok"), "fallback": (True, "ok")}),
    )
    result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"))
    assert result.status == "fallback"
    assert result.provider == "fallback"
    assert result.fallback is not None
    assert result.fallback["attempts"][0]["provider"] == "primary"


def test_capability_mismatch_skips_provider() -> None:
    providers = {
        "weak": provider("weak", ["general_reasoning"]),
        "strong": provider("strong", ["architecture_design"]),
    }
    rules = {
        "architecture_design": RoutingRule(
            "architecture_design",
            prefer=["weak", "strong"],
            required_capabilities=["architecture_design"],
        )
    }
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({pid: (True, "ok") for pid in providers}),
    )
    result = engine.route(ProviderRequest(task_type="architecture_design", prompt="design"), dry_run=True)
    assert result.provider == "strong"
    assert any("missing capabilities" in log for log in result.logs)


def test_cloud_disallowed_policy_skips_cloud_provider() -> None:
    providers = {
        "cloud": provider("cloud", ["general_reasoning"], allow_cloud=True),
        "local": provider("local", ["general_reasoning"], allow_cloud=False),
    }
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["cloud", "local"], allow_cloud=True)}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({pid: (True, "ok") for pid in providers}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="sensitive",
        policy=RoutePolicy(allow_cloud=False),
    )
    result = engine.route(request, dry_run=True)
    assert result.provider == "local"
    assert any("cloud providers disallowed" in log for log in result.logs)


def test_openai_compatible_request_formatting() -> None:
    cfg = provider("openrouter", ["general_reasoning"])
    adapter = OpenAICompatibleAdapter(cfg)
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hello",
        temperature=0.7,
        max_tokens=123,
        tools=[{"type": "function", "function": {"name": "x"}}],
    )
    payload = adapter.build_chat_payload(request, "test/model")
    assert payload["model"] == "test/model"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0.7
    assert payload["max_tokens"] == 123
    assert payload["tools"][0]["function"]["name"] == "x"


def test_openai_compatible_url_construction() -> None:
    cfg = ProviderConfig(
        provider_id="cursor_worker",
        enabled=True,
        provider_type="openai-compatible",
        base_url="http://localhost:8781/v1",
        health_check_endpoint="/health",
        default_model="cursor/active",
        requires_auth=False,
    )
    adapter = OpenAICompatibleAdapter(cfg)
    assert adapter.health_url() == "http://localhost:8781/health"
    assert adapter.chat_completions_url() == "http://localhost:8781/v1/chat/completions"
    assert adapter.models_url() == "http://localhost:8781/v1/models"


def test_health_check_success_and_failure(monkeypatch: Any) -> None:
    calls: list[str] = []

    def fake_urlopen(request: Any, timeout: float = 0) -> FakeHTTPResponse:
        calls.append(request.full_url)
        if request.full_url.endswith("/health"):
            return FakeHTTPResponse({"ok": True}, status=200)
        return FakeHTTPResponse({}, status=500)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    cfg = ProviderConfig(
        provider_id="worker",
        enabled=True,
        provider_type="openai-compatible",
        base_url="http://localhost:8781/v1",
        health_check_endpoint="/health",
        default_model="worker/model",
        requires_auth=False,
    )
    ok, reason = OpenAICompatibleAdapter(cfg).health_check()
    assert ok is True
    assert "healthy" in reason
    assert calls == ["http://localhost:8781/health"]


def test_list_models_uses_v1_models(monkeypatch: Any) -> None:
    calls: list[str] = []

    def fake_urlopen(request: Any, timeout: float = 0) -> FakeHTTPResponse:
        calls.append(request.full_url)
        return FakeHTTPResponse({"data": [{"id": "model-a"}, {"id": "model-b"}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    cfg = ProviderConfig(
        provider_id="worker",
        enabled=True,
        provider_type="openai-compatible",
        base_url="http://localhost:8781/v1",
        default_model="worker/model",
        requires_auth=False,
    )
    assert OpenAICompatibleAdapter(cfg).list_models() == ["model-a", "model-b"]
    assert calls == ["http://localhost:8781/v1/models"]


def test_invoke_posts_openai_payload_and_normalizes(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> FakeHTTPResponse:
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeHTTPResponse(
            {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1},
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    cfg = ProviderConfig(
        provider_id="worker",
        enabled=True,
        provider_type="openai-compatible",
        base_url="http://localhost:8781/v1",
        default_model="worker/model",
        requires_auth=False,
    )
    response = OpenAICompatibleAdapter(cfg).invoke(ProviderRequest(task_type="general_reasoning", prompt="hello"))
    assert captured["url"] == "http://localhost:8781/v1/chat/completions"
    assert captured["method"] == "POST"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "hello"}]
    assert response.status == "success"
    assert response.content == "ok"
    assert response.usage["prompt_tokens"] == 3


def test_normalized_response_format() -> None:
    cfg = provider("openrouter", ["general_reasoning"])
    adapter = OpenAICompatibleAdapter(cfg)
    response = adapter.normalize_response(
        {
            "choices": [{"message": {"content": "answer", "tool_calls": [{"id": "call_1"}]}}],
            "usage": {"prompt_tokens": 10},
        },
        latency_ms=42,
        model="test/model",
    )
    data = response.to_dict()
    assert data["provider"] == "openrouter"
    assert data["model"] == "test/model"
    assert data["status"] == "success"
    assert data["content"] == "answer"
    assert data["tool_calls"] == [{"id": "call_1"}]
    assert data["usage"] == {"prompt_tokens": 10}
    assert data["latency_ms"] == 42


def test_normalize_response_error_object_is_error() -> None:
    cfg = provider("openrouter", ["general_reasoning"])
    response = OpenAICompatibleAdapter(cfg).normalize_response(
        {"error": {"message": "bad key"}},
        latency_ms=1,
        model="test/model",
    )
    assert response.status == "error"
    assert response.error == {"category": "provider_error", "message": "bad key"}


def test_normalize_response_empty_choices_is_error() -> None:
    cfg = provider("openrouter", ["general_reasoning"])
    response = OpenAICompatibleAdapter(cfg).normalize_response({"choices": []}, latency_ms=1, model="test/model")
    assert response.status == "error"
    assert response.error is not None
    assert response.error["category"] == "empty_response"


def test_normalize_response_malformed_message_is_error() -> None:
    cfg = provider("openrouter", ["general_reasoning"])
    response = OpenAICompatibleAdapter(cfg).normalize_response(
        {"choices": [{"message": {"tool_calls": []}}]},
        latency_ms=1,
        model="test/model",
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error["category"] == "malformed_response"


def test_missing_required_env_var_is_clear_error(monkeypatch: Any) -> None:
    monkeypatch.delenv("MISSING_PROVIDER_KEY", raising=False)
    cfg = provider(
        "cloud",
        ["general_reasoning"],
        api_key_env="MISSING_PROVIDER_KEY",
        requires_auth=True,
    )
    adapter = OpenAICompatibleAdapter(cfg)
    ok, reason = adapter.health_check()
    assert ok is False
    assert "MISSING_PROVIDER_KEY" in reason
    response = adapter.invoke(ProviderRequest(task_type="general_reasoning", prompt="hi"))
    assert response.status == "error"
    assert response.error is not None
    assert response.error["category"] == "missing_credentials"


def test_audit_event_contains_guardian_ready_fields() -> None:
    providers = {"local": provider("local", ["general_reasoning"], allow_cloud=False)}
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["local"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"local": FakeAdapter(providers["local"])},
        health_checker=ProviderHealthChecker({"local": (True, "ok")}),
    )
    result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=True)
    assert result.audit is not None
    assert result.audit["selected_provider"] == "local"
    assert result.audit["task_type"] == "general_reasoning"
    assert result.audit["effective_policy"]["allow_cloud"] is True
    assert result.audit["health_checked"] is False
    assert result.audit["guardian_checked"] is False
    assert result.audit["guardian_decision"] == "NOT_CHECKED"


def test_guardian_block_prevents_code_edit_with_allow_flags() -> None:
    providers = {"cursor_worker": provider("cursor_worker", ["repo_edit", "local_file_access"], allow_cloud=False)}
    rules = {
        "code_edit": RoutingRule(
            "code_edit",
            prefer=["cursor_worker"],
            required_capabilities=["repo_edit", "local_file_access"],
            allow_local_file_access=True,
            allow_code_modification=True,
        )
    }
    adapter = FakeAdapter(providers["cursor_worker"])
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"cursor_worker": adapter},
        health_checker=ProviderHealthChecker({"cursor_worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.BLOCK, reason="blocked by policy"),
    )
    request = ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
    )
    result = engine.route(request, dry_run=False)
    assert result.provider == "none"
    assert result.error == {"category": "guardian_block", "message": "blocked by policy"}
    assert result.audit is not None
    assert result.audit["guardian_checked"] is True
    assert result.audit["guardian_decision"] == "BLOCK"
    assert adapter.invoked is False


def test_guardian_review_required_prevents_invocation() -> None:
    providers = {"cursor_worker": provider("cursor_worker", ["repo_edit", "local_file_access"], allow_cloud=False)}
    rules = {
        "code_edit": RoutingRule(
            "code_edit",
            prefer=["cursor_worker"],
            required_capabilities=["repo_edit", "local_file_access"],
            allow_local_file_access=True,
            allow_code_modification=True,
        )
    }
    adapter = FakeAdapter(providers["cursor_worker"])
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"cursor_worker": adapter},
        health_checker=ProviderHealthChecker({"cursor_worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.REVIEW_REQUIRED, reason="human approval required"),
    )
    request = ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
    )
    result = engine.route(request, dry_run=False)
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "guardian_review_required"
    assert result.audit is not None
    assert result.audit["guardian_decision"] == "REVIEW_REQUIRED"
    assert adapter.invoked is False


def test_guardian_not_checked_prevents_dangerous_live_invocation() -> None:
    providers = {"cursor_worker": provider("cursor_worker", ["repo_edit", "local_file_access"], allow_cloud=False)}
    rules = {
        "code_edit": RoutingRule(
            "code_edit",
            prefer=["cursor_worker"],
            required_capabilities=["repo_edit", "local_file_access"],
            allow_local_file_access=True,
            allow_code_modification=True,
        )
    }
    adapter = FakeAdapter(providers["cursor_worker"])
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"cursor_worker": adapter},
        health_checker=ProviderHealthChecker({"cursor_worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.NOT_CHECKED, reason="not checked"),
    )
    request = ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
    )
    result = engine.route(request, dry_run=False)
    assert result.status == "error"
    assert result.error == {"category": "guardian_not_checked", "message": "not checked"}
    assert adapter.invoked is False


def test_guardian_allow_permits_dangerous_invocation_when_policy_allows() -> None:
    providers = {"cursor_worker": provider("cursor_worker", ["repo_edit", "local_file_access"], allow_cloud=False)}
    rules = {
        "code_edit": RoutingRule(
            "code_edit",
            prefer=["cursor_worker"],
            required_capabilities=["repo_edit", "local_file_access"],
            allow_local_file_access=True,
            allow_code_modification=True,
        )
    }
    adapter = FakeAdapter(providers["cursor_worker"])
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"cursor_worker": adapter},
        health_checker=ProviderHealthChecker({"cursor_worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.ALLOW, reason="approved"),
    )
    request = ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
    )
    result = engine.route(request, dry_run=False)
    assert result.provider == "cursor_worker"
    assert result.status == "success"
    assert result.audit is not None
    assert result.audit["guardian_decision"] == "ALLOW"
    assert adapter.invoked is True


def test_non_dangerous_general_reasoning_proceeds_without_guardian() -> None:
    providers = {"reasoner": provider("reasoner", ["general_reasoning"])}
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["reasoner"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"reasoner": FakeAdapter(providers["reasoner"])},
        health_checker=ProviderHealthChecker({"reasoner": (True, "ok")}),
    )
    result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=False)
    assert result.status == "success"
    assert result.audit is not None
    assert result.audit["guardian_checked"] is False


def test_general_reasoning_provider_with_unused_dangerous_capabilities_needs_no_guardian() -> None:
    providers = {
        "worker": provider(
            "worker",
            ["general_reasoning", "terminal", "repo_edit", "local_file_access"],
            allow_cloud=False,
        )
    }
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.NOT_CHECKED),
    )
    result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=False)
    assert result.status == "success"
    assert result.audit is not None
    assert result.audit["guardian_decision"] == "NOT_CHECKED"


def test_audit_sink_receives_success_event() -> None:
    events: list[dict[str, Any]] = []
    sink = MemoryAuditSink(events)
    providers = {"reasoner": provider("reasoner", ["general_reasoning"])}
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["reasoner"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"reasoner": FakeAdapter(providers["reasoner"])},
        health_checker=ProviderHealthChecker({"reasoner": (True, "ok")}),
        audit_sink=sink,
    )
    engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=True)
    assert len(events) == 1
    assert events[0]["invocation_status"] == "success"


def test_audit_sink_receives_error_event() -> None:
    events: list[dict[str, Any]] = []
    sink = MemoryAuditSink(events)
    providers = {"editor": provider("editor", ["repo_edit"], allow_cloud=False)}
    rules = {"code_edit": RoutingRule("code_edit", prefer=["editor"], required_capabilities=["repo_edit"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"editor": FakeAdapter(providers["editor"])},
        health_checker=ProviderHealthChecker({"editor": (True, "ok")}),
        audit_sink=sink,
    )
    result = engine.route(ProviderRequest(task_type="code_edit", prompt="edit"), dry_run=True)
    assert result.status == "error"
    assert len(events) == 1
    assert events[0]["error_category"] == "no_eligible_provider"


def test_audit_jsonl_omits_secret_like_fields(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    sink = JsonlAuditSink(path)
    sink.emit(
        {
            "selected_provider": "p",
            "api_key_env": "SECRET_ENV",
            "headers": {"Authorization": "Bearer secret"},
            "nested": {"safe": "ok", "password": "bad"},
        }
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    assert "api_key_env" not in record
    assert "Authorization" not in record["headers"]
    assert record["nested"] == {"safe": "ok"}


def test_audit_redacts_secret_like_values() -> None:
    events: list[dict[str, Any]] = []
    sink = MemoryAuditSink(events)
    sink.emit(
        {
            "safe": "Authorization: Bearer abc.def",
            "fallback_attempts": [
                {
                    "reason": (
                        "provider said sk-testsecret123 token=rawvalue x-api-key: fakevalue "
                        "OPENAI_API_KEY=fakevalue ghp_fakevalue123456 "
                        "eyJhbGciOiJIUzI1NiJ9.abcdefghijklmnopqrstuv.abcdefghijklmnopqrstuv "
                        '"api_key": "json-secret"'
                    )
                }
            ],
            "nested": [
                {"message": "password: hunter2"},
                {"api_key": "removed"},
                {"headers": ["x-api-key: fakevalue\nAuthorization = Bearer abc.def.ghi"]},
            ],
        }
    )
    raw = json.dumps(events)
    assert "fakevalue" not in raw
    assert "ghp_fakevalue123456" not in raw
    assert "eyJhbGci" not in raw
    assert "json-secret" not in raw
    assert "hunter2" not in raw
    assert "removed" not in raw
    assert "[REDACTED]" in raw


def test_audit_redacts_additional_secret_patterns_without_usage_counters() -> None:
    events: list[dict[str, Any]] = []
    sink = MemoryAuditSink(events)
    sink.emit(
        {
            "reason": (
                "client_secret=fake-client access_key=fake-access Authorization: Basic Zm9vOmJhcg== "
                "callback=https://user:password@example.com/path lower_secret=fake-lower AKIA1234567890ABCD"
            ),
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
    )
    raw = json.dumps(events)
    assert "fake-client" not in raw
    assert "fake-access" not in raw
    assert "Zm9vOmJhcg" not in raw
    assert "user:password" not in raw
    assert "fake-lower" not in raw
    assert "AKIA1234567890ABCD" not in raw
    assert events[0]["usage"] == {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}


def test_audit_jsonl_writes_sanitized_values_only(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    JsonlAuditSink(path).emit({"reason": "Bearer abc.def and api_key=rawsecret", "api_key": "removed"})
    raw = path.read_text(encoding="utf-8")
    assert "abc.def" not in raw
    assert "rawsecret" not in raw
    assert "removed" not in raw
    assert "[REDACTED]" in raw


def test_allow_cloud_false_localhost_passes(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  local:
    enabled: true
    type: openai-compatible
    base_url: http://localhost:8781/v1
    default_model: local/model
    allow_cloud: false
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["local"].allow_cloud is False


def test_allow_cloud_false_loopback_ip_passes(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  local:
    enabled: true
    type: openai-compatible
    base_url: http://127.0.0.1:8781/v1
    default_model: local/model
    allow_cloud: false
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["local"].base_url == "http://127.0.0.1:8781/v1"


def test_loopback_only_trust_boundary_accepts_loopback(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  local:
    enabled: true
    type: openai-compatible
    base_url: http://127.0.0.1:8781/v1
    default_model: local/model
    allow_cloud: false
    local_trust_boundary: loopback_only
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["local"].local_trust_boundary == "loopback_only"


def test_loopback_only_trust_boundary_rejects_private_lan(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  lan:
    enabled: true
    type: openai-compatible
    base_url: http://192.168.1.2:8781/v1
    default_model: lan/model
    allow_cloud: false
    local_trust_boundary: loopback_only
    requires_auth: false
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_provider_registry(path)


def test_private_network_trust_boundary_accepts_private_lan(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  lan:
    enabled: true
    type: openai-compatible
    base_url: http://192.168.1.2:8781/v1
    default_model: lan/model
    allow_cloud: false
    local_trust_boundary: private_network
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["lan"].base_url == "http://192.168.1.2:8781/v1"


def test_explicit_allowlist_trust_boundary_accepts_allowed_host(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  allowed:
    enabled: true
    type: openai-compatible
    base_url: http://bridge.internal:8781/v1
    default_model: allowed/model
    allow_cloud: false
    local_trust_boundary: explicit_allowlist
    allowed_hosts:
      - bridge.internal
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["allowed"].base_url == "http://bridge.internal:8781/v1"


def test_explicit_allowlist_trust_boundary_matches_host_case_insensitively(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  allowed:
    enabled: true
    type: openai-compatible
    base_url: http://Bridge.Internal:8781/v1
    default_model: allowed/model
    allow_cloud: false
    local_trust_boundary: explicit_allowlist
    allowed_hosts:
      - bridge.internal
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["allowed"].base_url == "http://Bridge.Internal:8781/v1"


def test_explicit_allowlist_trust_boundary_rejects_unlisted_host(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  denied:
    enabled: true
    type: openai-compatible
    base_url: http://bridge.internal:8781/v1
    default_model: denied/model
    allow_cloud: false
    local_trust_boundary: explicit_allowlist
    allowed_hosts:
      - other.internal
    requires_auth: false
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_provider_registry(path)


def test_allow_cloud_false_public_hostname_fails(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  bad:
    enabled: true
    type: openai-compatible
    base_url: https://api.some-cloud.com/v1
    default_model: bad/model
    allow_cloud: false
    requires_auth: false
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_provider_registry(path)


def test_allow_cloud_true_public_hostname_passes(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  cloud:
    enabled: true
    type: openai-compatible
    base_url: https://api.some-cloud.com/v1
    default_model: cloud/model
    allow_cloud: true
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["cloud"].allow_cloud is True


def test_openai_compatible_base_url_rejects_non_http_scheme(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  bad:
    enabled: true
    type: openai-compatible
    base_url: file://localhost/path
    default_model: bad/model
    allow_cloud: false
    requires_auth: false
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_provider_registry(path)


def test_routing_rule_unknown_alias_fails_validation(tmp_path: Path) -> None:
    registry = tmp_path / "providers.yaml"
    rules = tmp_path / "rules.yaml"
    registry.write_text(
        """
providers:
  openrouter:
    enabled: true
    type: openrouter
    base_url: https://openrouter.ai/api/v1
    default_model: model/a
    available_models:
      - model/a
    model_aliases:
      known: model/a
    allow_cloud: true
    requires_auth: false
""",
        encoding="utf-8",
    )
    rules.write_text(
        """
routing_rules:
  general_reasoning:
    prefer:
      - openrouter.unknown
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_orchestration_config(registry, rules)


def test_missing_optional_provider_reference_does_not_block_startup(tmp_path: Path) -> None:
    registry = tmp_path / "providers.yaml"
    rules = tmp_path / "rules.yaml"
    registry.write_text(
        """
providers:
  copilot:
    enabled: true
    type: copilot
    base_url: http://localhost:8780/v1
    default_model: copilot/default
    capabilities:
      - general_reasoning
    fallback_provider: openrouter
    allow_cloud: true
    requires_auth: false
  local_ollama_worker:
    enabled: true
    type: openai-compatible
    base_url: http://localhost:11434/v1
    default_model: local/model
    capabilities:
      - general_reasoning
    allow_cloud: false
    requires_auth: false
""",
        encoding="utf-8",
    )
    rules.write_text(
        """
routing_rules:
  general_reasoning:
    prefer:
      - openrouter.claude_sonnet
      - local_ollama_worker
    required_capabilities:
      - general_reasoning
    max_cost_tier: medium
""",
        encoding="utf-8",
    )
    providers, loaded_rules = load_orchestration_config(registry, rules)
    issues = validate_route_consistency(providers, loaded_rules)
    assert "openrouter" not in providers
    assert any("fallback_provider openrouter is not registered" in issue for issue in issues)
    assert any("preferred provider openrouter.claude_sonnet is not registered" in issue for issue in issues)

    engine = RoutingEngine(
        providers,
        loaded_rules,
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({pid: (True, "ok") for pid in providers}),
    )
    result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=True)
    assert result.provider == "local_ollama_worker"


def test_preferred_provider_unknown_alias_returns_structured_error() -> None:
    providers = {
        "openrouter": provider(
            "openrouter",
            ["general_reasoning"],
            metadata={"model_aliases": {"known": "openrouter/model"}},
        )
    }
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["openrouter"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"openrouter": FakeAdapter(providers["openrouter"])},
        health_checker=ProviderHealthChecker({"openrouter": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hi",
        policy=RoutePolicy(preferred_provider="openrouter.unknown"),
    )
    result = engine.route(request, dry_run=True)
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "invalid_model_reference"


def test_preferred_provider_unknown_provider_returns_structured_error() -> None:
    providers = {"local": provider("local", ["general_reasoning"], allow_cloud=False)}
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["local"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"local": FakeAdapter(providers["local"])},
        health_checker=ProviderHealthChecker({"local": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hi",
        policy=RoutePolicy(preferred_provider="unknown_provider"),
    )
    result = engine.route(request, dry_run=True)
    assert result.status == "error"
    assert result.error == {
        "category": "invalid_provider_reference",
        "message": "unknown provider reference 'unknown_provider'",
    }


def test_preferred_provider_known_alias_resolves() -> None:
    providers = {
        "openrouter": provider(
            "openrouter",
            ["general_reasoning"],
            metadata={"model_aliases": {"known": "openrouter/model"}},
        )
    }
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["openrouter"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"openrouter": FakeAdapter(providers["openrouter"])},
        health_checker=ProviderHealthChecker({"openrouter": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hi",
        policy=RoutePolicy(preferred_provider="openrouter.known"),
    )
    result = engine.route(request, dry_run=True)
    assert result.status == "success"
    assert result.model == "openrouter/model"


def test_require_preferred_provider_unhealthy_does_not_fallback() -> None:
    providers = {
        "preferred": provider("preferred", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["preferred", "fallback"])},
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"preferred": (False, "down"), "fallback": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(preferred_provider="preferred", require_preferred_provider=True),
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "preferred_provider_unavailable"
    assert result.provider == "none"


def test_require_preferred_provider_adapter_error_does_not_fallback() -> None:
    providers = {
        "preferred": provider("preferred", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    adapters = {"preferred": FakeAdapter(providers["preferred"], status="error"), "fallback": FakeAdapter(providers["fallback"])}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["preferred", "fallback"])},
        adapters=adapters,
        health_checker=ProviderHealthChecker({"preferred": (True, "ok"), "fallback": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(preferred_provider="preferred", require_preferred_provider=True),
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "preferred_provider_unavailable"
    assert adapters["fallback"].invoked is False


def test_no_fallback_stops_after_first_candidate_failure() -> None:
    providers = {
        "primary": provider("primary", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    adapters = {"primary": FakeAdapter(providers["primary"], status="error"), "fallback": FakeAdapter(providers["fallback"])}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["primary", "fallback"])},
        adapters=adapters,
        health_checker=ProviderHealthChecker({"primary": (True, "ok"), "fallback": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(no_fallback=True),
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "fallback_disabled"
    assert adapters["fallback"].invoked is False


def test_default_preferred_provider_behavior_still_falls_back() -> None:
    providers = {
        "preferred": provider("preferred", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["preferred", "fallback"])},
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"preferred": (False, "down"), "fallback": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(preferred_provider="preferred"),
        ),
        dry_run=False,
    )
    assert result.status == "fallback"
    assert result.provider == "fallback"


def test_select_require_preferred_provider_unhealthy_does_not_fallback() -> None:
    providers = {
        "preferred": provider("preferred", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["preferred", "fallback"])},
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"preferred": (False, "down"), "fallback": (True, "ok")}),
    )
    candidate, logs = engine.select(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(preferred_provider="preferred", require_preferred_provider=True),
        )
    )
    assert candidate is None
    assert any("fallback disabled" in log for log in logs)
    assert not any("selected fallback" in log for log in logs)


def test_select_no_fallback_first_candidate_unhealthy_does_not_fallback() -> None:
    providers = {
        "primary": provider("primary", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["primary", "fallback"])},
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"primary": (False, "down"), "fallback": (True, "ok")}),
    )
    candidate, logs = engine.select(
        ProviderRequest(task_type="general_reasoning", prompt="hi", policy=RoutePolicy(no_fallback=True))
    )
    assert candidate is None
    assert any("no_fallback is enabled" in log for log in logs)
    assert not any("selected fallback" in log for log in logs)


def test_select_default_still_falls_back() -> None:
    providers = {
        "primary": provider("primary", ["general_reasoning"], priority=10),
        "fallback": provider("fallback", ["general_reasoning"], priority=20),
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["primary", "fallback"])},
        adapters={pid: FakeAdapter(cfg) for pid, cfg in providers.items()},
        health_checker=ProviderHealthChecker({"primary": (False, "down"), "fallback": (True, "ok")}),
    )
    candidate, logs = engine.select(ProviderRequest(task_type="general_reasoning", prompt="hi"))
    assert candidate is not None
    assert candidate.provider_id == "fallback"
    assert any("selected fallback" in log for log in logs)


def test_known_alias_and_direct_model_resolve() -> None:
    cfg = provider(
        "openrouter",
        ["general_reasoning"],
        metadata={"model_aliases": {"known": "openrouter/model"}},
    )
    assert RoutingEngine._model_for(cfg, "known") == (True, "openrouter/model", "resolved model alias")
    assert RoutingEngine._model_for(cfg, "openrouter/model") == (True, "openrouter/model", "resolved direct model")
    assert RoutingEngine._model_for(cfg, None) == (True, "openrouter/model", "using default model")


def test_string_booleans_raise_config_error(tmp_path: Path) -> None:
    for field in ("enabled", "allow_cloud", "requires_auth"):
        path = tmp_path / f"{field}.yaml"
        path.write_text(
            f"""
providers:
  bad:
    enabled: true
    type: openai-compatible
    base_url: http://localhost:8781/v1
    default_model: bad/model
    allow_cloud: true
    requires_auth: false
    {field}: "false"
""",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError):
            load_provider_registry(path)


def test_enabled_false_parses_false(tmp_path: Path) -> None:
    path = tmp_path / "providers.yaml"
    path.write_text(
        """
providers:
  disabled:
    enabled: false
    type: openai-compatible
    base_url: http://localhost:8781/v1
    default_model: disabled/model
    allow_cloud: true
    requires_auth: false
""",
        encoding="utf-8",
    )
    assert load_provider_registry(path)["disabled"].enabled is False


def test_routing_rule_allow_cloud_false_parses_false(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(
        """
routing_rules:
  general_reasoning:
    allow_cloud: false
""",
        encoding="utf-8",
    )
    assert load_routing_rules(path)["general_reasoning"].allow_cloud is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("allow_cloud", '"false"'),
        ("allow_local_file_access", '"false"'),
        ("allow_code_modification", '"true"'),
        ("allow_terminal_execution", '"false"'),
    ],
)
def test_routing_rule_string_booleans_raise_config_error(tmp_path: Path, field: str, value: str) -> None:
    path = tmp_path / "rules.yaml"
    path.write_text(
        f"""
routing_rules:
  general_reasoning:
    {field}: {value}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_routing_rules(path)


def test_explicit_terminal_tool_manifest_requires_policy_and_guardian_for_live_route() -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "terminal"], allow_cloud=False)}
    adapter = FakeAdapter(providers["worker"])
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": adapter},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.NOT_CHECKED, reason="not checked"),
    )
    denied = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"type": "function", "function": {"name": "safe_lookup"}, "capabilities": ["terminal"]}],
        ),
        dry_run=False,
    )
    assert denied.status == "error"
    assert adapter.invoked is False

    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(allow_terminal_execution=True),
            tools=[{"type": "function", "function": {"name": "safe_lookup"}, "capabilities": ["terminal"]}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "guardian_not_checked"
    assert adapter.invoked is False


def test_explicit_repo_edit_tool_manifest_requires_policy_and_guardian() -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "repo_edit"], allow_cloud=False)}
    adapter = FakeAdapter(providers["worker"])
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": adapter},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.NOT_CHECKED),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"function": {"name": "safe_lookup", "x-hermes-capabilities": ["repo_edit"]}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert any("code modification" in log for log in result.logs)

    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(allow_code_modification=True),
            tools=[{"function": {"name": "safe_lookup", "x-hermes-capabilities": ["repo_edit"]}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "guardian_not_checked"
    assert adapter.invoked is False


def test_explicit_local_file_tool_manifest_requires_local_file_policy() -> None:
    providers = {
        "worker": provider("worker", ["general_reasoning", "filesystem", "local_file_access"], allow_cloud=False)
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"metadata": {"capabilities": ["local_file_access"]}, "function": {"name": "lookup"}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert any("local file access" in log for log in result.logs)


def test_tool_classifier_splits_camel_kebab_dotted_and_url_names() -> None:
    assert {"filesystem", "local_file_access"}.issubset(classify_tools([{"function": {"name": "readFile"}}]))
    assert {"repo_edit", "filesystem", "local_file_access"}.issubset(
        classify_tools([{"function": {"name": "writeText"}}])
    )
    assert "mcp_tools" in classify_tools([{"function": {"name": "open-url"}}])
    assert {"filesystem", "local_file_access"}.issubset(classify_tools([{"function": {"name": "fs.glob"}}]))
    assert "terminal" in classify_tools([{"function": {"name": "powershell"}}])
    assert "mcp_tools" in classify_tools([{"function": {"name": "httpClient"}}])


def test_unknown_explicit_tool_capability_returns_structured_error() -> None:
    providers = {"reasoner": provider("reasoner", ["general_reasoning"])}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["reasoner"])},
        adapters={"reasoner": FakeAdapter(providers["reasoner"])},
        health_checker=ProviderHealthChecker({"reasoner": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"function": {"name": "lookup"}, "capabilities": ["made_up_capability"]}],
        ),
        dry_run=True,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "invalid_tool_capability"


@pytest.mark.parametrize("capability", ["general_reasoning", "creative_generation"])
def test_explicit_tool_manifest_rejects_provider_task_capabilities(capability: str) -> None:
    providers = {"reasoner": provider("reasoner", ["general_reasoning"])}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["reasoner"])},
        adapters={"reasoner": FakeAdapter(providers["reasoner"])},
        health_checker=ProviderHealthChecker({"reasoner": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"function": {"name": "harmless_lookup"}, "capabilities": [capability]}],
        ),
        dry_run=True,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "invalid_tool_capability"


def test_general_reasoning_with_harmless_tools_passes() -> None:
    providers = {"reasoner": provider("reasoner", ["general_reasoning"])}
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["reasoner"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"reasoner": FakeAdapter(providers["reasoner"])},
        health_checker=ProviderHealthChecker({"reasoner": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hi",
        tools=[{"type": "function", "function": {"name": "lookup_weather"}}],
    )
    assert engine.route(request, dry_run=False).status == "success"


def test_general_reasoning_shell_tool_without_terminal_permission_rejects() -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "terminal"], allow_cloud=False)}
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hi",
        tools=[{"type": "function", "function": {"name": "run_shell_command"}}],
    )
    result = engine.route(request, dry_run=False)
    assert result.status == "error"
    assert result.provider == "none"


def test_terminal_exec_tool_implies_terminal_and_requires_policy() -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "terminal"], allow_cloud=False)}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"type": "function", "function": {"name": "terminal_exec"}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.provider == "none"
    assert any("terminal" in log and "disallowed" in log for log in result.logs)


def test_explicit_harmless_tool_manifest_does_not_suppress_terminal_inference() -> None:
    providers = {
        "worker": provider(
            "worker",
            ["general_reasoning", "terminal", "filesystem", "local_file_access"],
            allow_cloud=False,
        )
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(allow_local_file_access=True),
            tools=[{"function": {"name": "terminal_exec"}, "capabilities": ["local_file_access"]}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert any("terminal" in log and "disallowed" in log for log in result.logs)


def test_explicit_harmless_tool_manifest_does_not_suppress_write_inference() -> None:
    providers = {
        "worker": provider(
            "worker",
            ["general_reasoning", "repo_edit", "filesystem", "local_file_access"],
            allow_cloud=False,
        )
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(allow_local_file_access=True),
            tools=[{"function": {"name": "writeFile"}, "capabilities": ["local_file_access"]}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert any("code modification" in log and "disallowed" in log for log in result.logs)


def test_explicit_terminal_tool_manifest_requires_terminal_policy_on_harmless_name() -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "terminal"], allow_cloud=False)}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"function": {"name": "harmless_lookup"}, "capabilities": ["terminal"]}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert any("terminal" in log and "disallowed" in log for log in result.logs)


def test_explicit_test_runner_tool_manifest_requires_execution_permission() -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "test_runner"], allow_cloud=False)}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"function": {"name": "harmless_lookup"}, "capabilities": ["test_runner"]}],
        ),
        dry_run=True,
    )
    assert result.provider == "none"
    assert any("terminal" in log and "disallowed" in log for log in result.logs)


def test_read_path_tool_implies_local_file_access_and_requires_policy() -> None:
    providers = {
        "worker": provider("worker", ["general_reasoning", "filesystem", "local_file_access"], allow_cloud=False)
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"type": "function", "function": {"name": "read_path"}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.provider == "none"
    assert any("local file access" in log or "filesystem" in log for log in result.logs)


@pytest.mark.parametrize("tool_name", ["save_file", "modify_file"])
def test_file_modification_tool_implies_repo_edit_and_requires_policy(tool_name: str) -> None:
    providers = {
        "worker": provider(
            "worker",
            ["general_reasoning", "filesystem", "local_file_access", "repo_edit"],
            allow_cloud=False,
        )
    }
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(allow_local_file_access=True),
            tools=[{"type": "function", "function": {"name": tool_name}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.provider == "none"
    assert any("code modification" in log and "disallowed" in log for log in result.logs)


@pytest.mark.parametrize("tool_name", ["http_request", "fetch_url", "browser_open"])
def test_network_tool_implies_mcp_tools_and_requires_policy(tool_name: str) -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "mcp_tools"], allow_cloud=False)}
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": FakeAdapter(providers["worker"])},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            tools=[{"type": "function", "function": {"name": tool_name}}],
        ),
        dry_run=True,
    )
    assert result.provider == "none"
    assert any("MCP tool exposure disallowed" in log for log in result.logs)


@pytest.mark.parametrize("tool_name", ["http_request", "fetch_url", "browser_open"])
def test_network_tool_with_mcp_allow_still_requires_guardian_for_live_route(tool_name: str) -> None:
    providers = {"worker": provider("worker", ["general_reasoning", "mcp_tools"], allow_cloud=False)}
    adapter = FakeAdapter(providers["worker"])
    engine = RoutingEngine(
        providers,
        {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])},
        adapters={"worker": adapter},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.NOT_CHECKED, reason="not checked"),
    )
    result = engine.route(
        ProviderRequest(
            task_type="general_reasoning",
            prompt="hi",
            policy=RoutePolicy(allow_mcp_tools=True),
            tools=[{"type": "function", "function": {"name": tool_name}}],
        ),
        dry_run=False,
    )
    assert result.status == "error"
    assert result.error is not None
    assert result.error["category"] == "guardian_not_checked"
    assert adapter.invoked is False


def test_code_edit_patch_tool_requires_policy_and_guardian_allow() -> None:
    providers = {
        "editor": provider(
            "editor",
            ["general_reasoning", "repo_edit", "local_file_access", "filesystem"],
            allow_cloud=False,
        )
    }
    rules = {"code_edit": RoutingRule("code_edit", prefer=["editor"], required_capabilities=["general_reasoning"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"editor": FakeAdapter(providers["editor"])},
        health_checker=ProviderHealthChecker({"editor": (True, "ok")}),
        guardian_checker=StaticGuardian(GuardianDecision.ALLOW),
    )
    request = ProviderRequest(
        task_type="code_edit",
        prompt="edit",
        policy=RoutePolicy(allow_local_file_access=True, allow_code_modification=True),
        tools=[{"type": "function", "function": {"name": "apply_patch_write_file"}}],
    )
    result = engine.route(request, dry_run=False)
    assert result.status == "success"
    assert result.audit is not None
    assert result.audit["guardian_decision"] == "ALLOW"


def test_request_tools_are_not_forwarded_when_policy_denies() -> None:
    class CapturingAdapter(FakeAdapter):
        invoked = False

        def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
            self.invoked = True
            return super().invoke(request, model)

    providers = {"worker": provider("worker", ["general_reasoning", "terminal"], allow_cloud=False)}
    adapter = CapturingAdapter(providers["worker"])
    rules = {"general_reasoning": RoutingRule("general_reasoning", prefer=["worker"])}
    engine = RoutingEngine(
        providers,
        rules,
        adapters={"worker": adapter},
        health_checker=ProviderHealthChecker({"worker": (True, "ok")}),
    )
    request = ProviderRequest(
        task_type="general_reasoning",
        prompt="hi",
        tools=[{"type": "function", "function": {"name": "terminal_exec"}}],
    )
    result = engine.route(request, dry_run=False)
    assert result.status == "error"
    assert adapter.invoked is False


class MockBridgeHandler(BaseHTTPRequestHandler):
    posts: list[dict[str, Any]] = []
    error_mode = False

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send({"ok": True})
        elif self.path == "/v1/models":
            self._send({"data": [{"id": "mock/model"}]})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.posts.append(payload)
        if self.error_mode:
            self._send({"error": {"message": "mock provider error"}})
        else:
            self._send({"choices": [{"message": {"content": "mock ok"}}], "usage": {"prompt_tokens": 1}})

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_mock_bridge(error_mode: bool = False) -> tuple[ThreadingHTTPServer, str]:
    handler = type("BridgeHandler", (MockBridgeHandler,), {"posts": [], "error_mode": error_mode})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}/v1"


def test_mock_http_bridge_health_and_invoke() -> None:
    server, base_url = start_mock_bridge()
    try:
        cfg = provider("mock_bridge", ["general_reasoning"], base_url=base_url, requires_auth=False)
        engine = RoutingEngine(
            {"mock_bridge": cfg},
            {"general_reasoning": RoutingRule("general_reasoning", prefer=["mock_bridge"])},
        )
        result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=False)
        assert result.status == "success"
        assert result.content == "mock ok"
        assert result.health_checked is True
    finally:
        server.shutdown()


def test_mock_http_bridge_list_models_uses_real_server() -> None:
    server, base_url = start_mock_bridge()
    try:
        cfg = provider("mock_bridge", ["general_reasoning"], base_url=base_url, requires_auth=False)
        assert OpenAICompatibleAdapter(cfg).list_models() == ["mock/model"]
    finally:
        server.shutdown()


def test_local_bridge_health_url_uses_service_root_health() -> None:
    cfg = provider("mock_bridge", ["general_reasoning"], base_url="http://127.0.0.1:8781/v1", requires_auth=False)
    cfg = ProviderConfig(**{**cfg.__dict__, "health_check_endpoint": "/health"})
    assert OpenAICompatibleAdapter(cfg).health_url() == "http://127.0.0.1:8781/health"


def test_openrouter_health_url_keeps_models_under_api_v1() -> None:
    cfg = provider(
        "openrouter",
        ["general_reasoning"],
        base_url="https://openrouter.ai/api/v1",
        requires_auth=False,
    )
    cfg = ProviderConfig(**{**cfg.__dict__, "health_check_endpoint": "/models"})
    assert OpenAICompatibleAdapter(cfg).health_url() == "https://openrouter.ai/api/v1/models"


def test_mock_http_bridge_fallback_after_provider_error() -> None:
    primary_server, primary_url = start_mock_bridge(error_mode=True)
    fallback_server, fallback_url = start_mock_bridge()
    try:
        providers = {
            "primary": provider("primary", ["general_reasoning"], base_url=primary_url, requires_auth=False),
            "fallback": provider("fallback", ["general_reasoning"], base_url=fallback_url, requires_auth=False),
        }
        engine = RoutingEngine(
            providers,
            {"general_reasoning": RoutingRule("general_reasoning", prefer=["primary", "fallback"])},
        )
        result = engine.route(ProviderRequest(task_type="general_reasoning", prompt="hi"), dry_run=False)
        assert result.status == "fallback"
        assert result.provider == "fallback"
        assert result.content == "mock ok"
    finally:
        primary_server.shutdown()
        fallback_server.shutdown()


def test_cli_dry_run_reports_unverified_availability() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hermes.py",
            "route",
            "--task",
            "code_edit",
            "--prompt",
            "permission smoke test: explicit allow",
            "--allow-local-file-access",
            "--allow-code-modification",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["provider"] == "cursor_worker"
    assert payload["dry_run"] is True
    assert payload["health_checked"] is False
    assert payload["audit"]["health_checked"] is False
    assert "provider availability was not verified" in "\n".join(payload["logs"])


def test_cli_accepts_strict_fallback_policy_flags() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hermes.py",
            "route",
            "--task",
            "general_reasoning",
            "--prompt",
            "strict policy smoke",
            "--preferred-provider",
            "copilot",
            "--require-preferred-provider",
            "--no-fallback",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["audit"]["effective_policy"]["require_preferred_provider"] is True
    assert payload["audit"]["effective_policy"]["no_fallback"] is True


def test_cli_validate_config_reports_no_issues_for_current_config() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hermes.py",
            "route",
            "--validate-config",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {"issues": []}


def test_cli_accepts_allow_mcp_tools_and_records_policy() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hermes.py",
            "route",
            "--task",
            "long_context_review",
            "--prompt",
            "mcp policy smoke",
            "--capability",
            "mcp_tools",
            "--allow-mcp-tools",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["audit"]["effective_policy"]["allow_mcp_tools"] is True
