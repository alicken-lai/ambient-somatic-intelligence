"""Provider adapter abstractions."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from hermes.orchestration.models import HermesResponse, ProviderConfig, ProviderRequest


class ProviderAdapter(ABC):
    """Common interface for exposed providers, bridges, and agents."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.provider_id

    @property
    def type(self) -> str:
        return self.config.provider_type

    @property
    def capabilities(self) -> list[str]:
        return self.config.capabilities

    @abstractmethod
    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        """Return health status and a human-readable reason."""

    def list_models(self) -> list[str]:
        return list(self.config.available_models)

    @abstractmethod
    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        """Invoke the provider and return a normalized Hermes response."""

    def estimate_cost(self, request: ProviderRequest) -> float | None:
        return None

    def supports(self, task: ProviderRequest) -> bool:
        return set(task.required_capabilities).issubset(set(self.capabilities))

    @abstractmethod
    def normalize_response(self, response: dict[str, Any], latency_ms: int, model: str | None) -> HermesResponse:
        """Convert provider-native response into HermesResponse."""


class OpenAICompatibleAdapter(ProviderAdapter):
    """Adapter for OpenAI-compatible /v1/chat/completions endpoints."""

    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        if not self.config.base_url:
            return False, "missing base_url"
        auth_ok, auth_reason = self._auth_ready()
        if not auth_ok:
            return False, auth_reason
        url = self._join_url(self.config.base_url, self.config.health_check_endpoint or "/health")
        try:
            request = urllib.request.Request(url, method="GET", headers=self._headers(include_json=False))
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                if 200 <= response.status < 300:
                    return True, f"healthy:{response.status}"
                return False, f"health status {response.status}"
        except (OSError, urllib.error.URLError) as exc:
            return False, str(exc)

    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        if not self.config.base_url:
            raise RuntimeError(f"provider {self.name} missing base_url")
        auth_ok, auth_reason = self._auth_ready()
        if not auth_ok:
            return HermesResponse(
                provider=self.name,
                model=model or self.config.default_model,
                status="error",
                content="",
                logs=[auth_reason],
                error={"category": "missing_credentials", "message": auth_reason},
            )
        selected_model = model or self.config.default_model
        payload = self.build_chat_payload(request, selected_model)
        url = self.chat_completions_url()
        body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(url, data=body, method="POST", headers=self._headers())
        started = time.time()
        try:
            with urllib.request.urlopen(http_request, timeout=60) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
            latency_ms = int((time.time() - started) * 1000)
            return self.normalize_response(data, latency_ms, selected_model)
        except Exception as exc:
            latency_ms = int((time.time() - started) * 1000)
            return HermesResponse(
                provider=self.name,
                model=selected_model,
                status="error",
                content="",
                latency_ms=latency_ms,
                logs=[f"invoke failed: {exc}"],
                error={"category": "invoke_failed", "message": str(exc)},
            )

    def list_models(self) -> list[str]:
        if not self.config.base_url:
            return super().list_models()
        auth_ok, _auth_reason = self._auth_ready()
        if not auth_ok:
            return super().list_models()
        request = urllib.request.Request(self.models_url(), method="GET", headers=self._headers(include_json=False))
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8") or "{}")
            raw_models = data.get("data", [])
            models = [item["id"] for item in raw_models if isinstance(item, dict) and item.get("id")]
            return models or super().list_models()
        except Exception:
            return super().list_models()

    def build_chat_payload(self, request: ProviderRequest, model: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model or self.config.default_model,
            "messages": request.chat_messages(),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            payload["tools"] = request.tools
        if request.stream:
            payload["stream"] = request.stream
        return payload

    def normalize_response(self, response: dict[str, Any], latency_ms: int, model: str | None) -> HermesResponse:
        if not isinstance(response, dict):
            return self._error_response("malformed_response", "provider response was not a JSON object", latency_ms, model)
        if response.get("error"):
            error = response["error"]
            message = error.get("message") if isinstance(error, dict) else str(error)
            return self._error_response("provider_error", message or "provider returned error object", latency_ms, model)
        if "content" in response and isinstance(response.get("content"), str):
            content = response["content"]
            tool_calls: list[dict[str, Any]] = []
        else:
            choices = response.get("choices")
            if not isinstance(choices, list) or not choices:
                return self._error_response("empty_response", "provider response missing non-empty choices", latency_ms, model)
            first = choices[0]
            if not isinstance(first, dict):
                return self._error_response("malformed_response", "first choice was not an object", latency_ms, model)
            message = first.get("message")
            if not isinstance(message, dict):
                return self._error_response("malformed_response", "first choice missing message object", latency_ms, model)
            content = message.get("content")
            if not isinstance(content, str):
                return self._error_response("malformed_response", "message content missing or not a string", latency_ms, model)
            tool_calls = message.get("tool_calls") or []
            if not isinstance(tool_calls, list):
                return self._error_response("malformed_response", "tool_calls was not a list", latency_ms, model)
        return HermesResponse(
            provider=self.name,
            model=model or response.get("model") or self.config.default_model,
            status="success",
            content=content,
            tool_calls=tool_calls,
            usage=response.get("usage") or {},
            latency_ms=latency_ms,
            logs=[f"normalized OpenAI-compatible response from {self.name}"],
        )

    def health_url(self) -> str:
        return self._join_url(self.config.base_url or "", self.config.health_check_endpoint or "/health")

    def chat_completions_url(self) -> str:
        return self._join_url(self.config.base_url or "", "/v1/chat/completions")

    def models_url(self) -> str:
        return self._join_url(self.config.base_url or "", "/v1/models")

    def _auth_ready(self) -> tuple[bool, str]:
        if self.config.api_key_env and self.config.requires_auth and not os.environ.get(self.config.api_key_env):
            return False, f"missing required env var {self.config.api_key_env} for provider {self.name}"
        return True, "auth ready"

    def _error_response(
        self,
        category: str,
        message: str,
        latency_ms: int,
        model: str | None,
    ) -> HermesResponse:
        return HermesResponse(
            provider=self.name,
            model=model or self.config.default_model,
            status="error",
            content="",
            latency_ms=latency_ms,
            logs=[message],
            error={"category": category, "message": message},
        )

    def _headers(self, include_json: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {}
        if include_json:
            headers["Content-Type"] = "application/json"
        if self.config.api_key_env:
            api_key = os.environ.get(self.config.api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        return headers

    @staticmethod
    def _join_url(base_url: str, path: str) -> str:
        base = base_url.rstrip("/")
        parsed_path = urllib.parse.urlparse(base).path.rstrip("/")
        if path.startswith("/v1/"):
            service_root = base[:-3] if parsed_path.endswith("/v1") else base
            return f"{service_root.rstrip('/')}{path}"
        if path.startswith("/"):
            if path == "/health":
                service_root = base[:-3] if parsed_path.endswith("/v1") else base
                return f"{service_root.rstrip('/')}{path}"
            return f"{base}{path}"
        return f"{base}/{path}"


class BridgeSpecAdapter(OpenAICompatibleAdapter):
    """OpenAI-compatible adapter used for IDE worker bridges."""


def adapter_for(config: ProviderConfig) -> ProviderAdapter:
    """Factory for known provider adapter types."""

    openai_like = {"openai-compatible", "openrouter", "copilot", "hermes-subagent", "mcp-agent"}
    if config.provider_type in openai_like:
        return OpenAICompatibleAdapter(config)
    if config.provider_type == "local-cli":
        return BridgeSpecAdapter(config)
    return OpenAICompatibleAdapter(config)
