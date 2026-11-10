"""Data models for Hermes provider orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


COST_TIERS = {"low": 1, "medium": 2, "high": 3}
LATENCY_TIERS = {"low": 1, "medium": 2, "high": 3}


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for one exposed provider endpoint or bridge."""

    provider_id: str
    enabled: bool
    provider_type: str
    base_url: str | None = None
    api_key_env: str | None = None
    default_model: str | None = None
    available_models: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    priority: int = 100
    cost_tier: str = "medium"
    latency_tier: str = "medium"
    context_window: int | None = None
    health_check_endpoint: str | None = None
    fallback_provider: str | None = None
    allow_cloud: bool = True
    local_trust_boundary: str = "private_network"
    requires_auth: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def supports_capabilities(self, required: set[str]) -> bool:
        return required.issubset(set(self.capabilities))


@dataclass(frozen=True)
class RoutingRule:
    """Routing preference and constraints for a task category."""

    task_type: str
    prefer: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    fallback_order: list[str] = field(default_factory=list)
    max_cost_tier: str | None = None
    allow_cloud: bool | None = None
    allow_local_file_access: bool | None = None
    allow_code_modification: bool | None = None
    allow_terminal_execution: bool | None = None


@dataclass(frozen=True)
class RoutePolicy:
    """Per-request governance and routing policy."""

    allow_cloud: bool = True
    allow_local_file_access: bool = False
    allow_code_modification: bool = False
    allow_terminal_execution: bool = False
    allow_mcp_tools: bool = False
    max_cost_tier: str = "high"
    preferred_provider: str | None = None
    require_preferred_provider: bool = False
    no_fallback: bool = False

    def with_rule_defaults(self, rule: RoutingRule | None) -> "RoutePolicy":
        if rule is None:
            return self
        rule_allows_cloud = True if rule.allow_cloud is None else rule.allow_cloud
        rule_cost = self.max_cost_tier if rule.max_cost_tier is None else rule.max_cost_tier
        rule_allows_local = True if rule.allow_local_file_access is None else rule.allow_local_file_access
        rule_allows_code = True if rule.allow_code_modification is None else rule.allow_code_modification
        rule_allows_terminal = True if rule.allow_terminal_execution is None else rule.allow_terminal_execution
        return RoutePolicy(
            allow_cloud=self.allow_cloud and rule_allows_cloud,
            allow_local_file_access=self.allow_local_file_access and rule_allows_local,
            allow_code_modification=self.allow_code_modification and rule_allows_code,
            allow_terminal_execution=self.allow_terminal_execution and rule_allows_terminal,
            allow_mcp_tools=self.allow_mcp_tools,
            max_cost_tier=min(self.max_cost_tier, rule_cost, key=lambda tier: COST_TIERS[tier]),
            preferred_provider=self.preferred_provider,
            require_preferred_provider=self.require_preferred_provider,
            no_fallback=self.no_fallback,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_cloud": self.allow_cloud,
            "allow_local_file_access": self.allow_local_file_access,
            "allow_code_modification": self.allow_code_modification,
            "allow_terminal_execution": self.allow_terminal_execution,
            "allow_mcp_tools": self.allow_mcp_tools,
            "max_cost_tier": self.max_cost_tier,
            "preferred_provider": self.preferred_provider,
            "require_preferred_provider": self.require_preferred_provider,
            "no_fallback": self.no_fallback,
        }


@dataclass(frozen=True)
class ProviderRequest:
    """Normalized request sent through Hermes routing."""

    task_type: str
    prompt: str
    messages: list[dict[str, str]] | None = None
    required_capabilities: list[str] = field(default_factory=list)
    policy: RoutePolicy = field(default_factory=RoutePolicy)
    temperature: float = 0.2
    max_tokens: int = 2048
    tools: list[dict[str, Any]] | None = None
    stream: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def chat_messages(self) -> list[dict[str, str]]:
        if self.messages:
            return self.messages
        return [{"role": "user", "content": self.prompt}]


@dataclass
class HermesResponse:
    """Provider-neutral response returned to Hermes."""

    provider: str
    model: str | None
    status: str
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    cost_estimate: float | None = None
    confidence: float | None = None
    logs: list[str] = field(default_factory=list)
    fallback: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    audit: dict[str, Any] | None = None
    dry_run: bool | None = None
    health_checked: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
            "cost_estimate": self.cost_estimate,
            "confidence": self.confidence,
            "logs": self.logs,
            "fallback": self.fallback,
            "error": self.error,
            "audit": self.audit,
            "dry_run": self.dry_run,
            "health_checked": self.health_checked,
        }
