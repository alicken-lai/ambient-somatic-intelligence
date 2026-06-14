"""YAML config loading and validation for Hermes provider routing."""

from __future__ import annotations

from pathlib import Path
import ipaddress
from typing import Any
import urllib.parse

import yaml

from hermes.orchestration.models import COST_TIERS, LATENCY_TIERS, ProviderConfig, RoutingRule


class ConfigError(ValueError):
    """Raised when provider orchestration config is invalid."""


LOCAL_TRUST_BOUNDARIES = {"loopback_only", "private_network", "explicit_allowlist"}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"Missing config file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a mapping: {path}")
    return data


def load_provider_registry(path: str | Path) -> dict[str, ProviderConfig]:
    """Load provider configs keyed by provider id."""

    data = _load_yaml(Path(path))
    raw_providers = data.get("providers", data)
    if not isinstance(raw_providers, dict):
        raise ConfigError("provider registry must contain a providers mapping")

    providers: dict[str, ProviderConfig] = {}
    for provider_id, raw in raw_providers.items():
        if not isinstance(raw, dict):
            raise ConfigError(f"provider {provider_id!r} must be a mapping")
        provider_type = raw.get("type") or raw.get("provider_type")
        if not provider_type:
            raise ConfigError(f"provider {provider_id!r} is missing type")
        cost_tier = raw.get("cost_tier", "medium")
        latency_tier = raw.get("latency_tier", "medium")
        if cost_tier not in COST_TIERS:
            raise ConfigError(f"provider {provider_id!r} has invalid cost_tier {cost_tier!r}")
        if latency_tier not in LATENCY_TIERS:
            raise ConfigError(f"provider {provider_id!r} has invalid latency_tier {latency_tier!r}")
        enabled = _strict_bool(raw.get("enabled", True), f"provider {provider_id!r} enabled")
        allow_cloud = _strict_bool(raw.get("allow_cloud", True), f"provider {provider_id!r} allow_cloud")
        requires_auth = _strict_bool(raw.get("requires_auth", True), f"provider {provider_id!r} requires_auth")
        local_trust_boundary = str(raw.get("local_trust_boundary", "private_network"))
        if local_trust_boundary not in LOCAL_TRUST_BOUNDARIES:
            raise ConfigError(f"provider {provider_id!r} has invalid local_trust_boundary {local_trust_boundary!r}")
        base_url = raw.get("base_url")
        if base_url and str(provider_type) == "openai-compatible":
            _validate_http_base_url_scheme(provider_id, str(base_url))
        if allow_cloud is False and str(provider_type) not in {"cli", "cli_or_builtin"}:
            _validate_local_base_url(
                provider_id,
                base_url,
                local_trust_boundary=local_trust_boundary,
                allowed_hosts=raw.get("allowed_hosts", []),
            )

        providers[provider_id] = ProviderConfig(
            provider_id=provider_id,
            enabled=enabled,
            provider_type=str(provider_type),
            base_url=base_url,
            api_key_env=raw.get("api_key_env"),
            default_model=raw.get("default_model"),
            available_models=list(raw.get("available_models", [])),
            capabilities=list(raw.get("capabilities", [])),
            priority=int(raw.get("priority", 100)),
            cost_tier=cost_tier,
            latency_tier=latency_tier,
            context_window=raw.get("context_window"),
            health_check_endpoint=raw.get("health_check_endpoint"),
            fallback_provider=raw.get("fallback_provider"),
            allow_cloud=allow_cloud,
            local_trust_boundary=local_trust_boundary,
            requires_auth=requires_auth,
            metadata={k: v for k, v in raw.items() if k not in _PROVIDER_FIELDS},
        )
    return providers


def load_routing_rules(path: str | Path) -> dict[str, RoutingRule]:
    """Load routing rules keyed by task category."""

    data = _load_yaml(Path(path))
    raw_rules = data.get("routing_rules", data)
    if not isinstance(raw_rules, dict):
        raise ConfigError("routing rules must contain a routing_rules mapping")

    rules: dict[str, RoutingRule] = {}
    for task_type, raw in raw_rules.items():
        if not isinstance(raw, dict):
            raise ConfigError(f"routing rule {task_type!r} must be a mapping")
        max_cost_tier = raw.get("max_cost_tier")
        if max_cost_tier is not None and max_cost_tier not in COST_TIERS:
            raise ConfigError(f"routing rule {task_type!r} has invalid max_cost_tier")
        rules[task_type] = RoutingRule(
            task_type=task_type,
            prefer=list(raw.get("prefer", [])),
            required_capabilities=list(raw.get("required_capabilities", [])),
            fallback_order=list(raw.get("fallback_order", [])),
            max_cost_tier=max_cost_tier,
            allow_cloud=_optional_strict_bool(raw.get("allow_cloud"), f"routing rule {task_type!r} allow_cloud"),
            allow_local_file_access=_optional_strict_bool(
                raw.get("allow_local_file_access"),
                f"routing rule {task_type!r} allow_local_file_access",
            ),
            allow_code_modification=_optional_strict_bool(
                raw.get("allow_code_modification"),
                f"routing rule {task_type!r} allow_code_modification",
            ),
            allow_terminal_execution=_optional_strict_bool(
                raw.get("allow_terminal_execution"),
                f"routing rule {task_type!r} allow_terminal_execution",
            ),
        )
    return rules


def load_orchestration_config(
    registry_path: str | Path = "config/provider_registry.yaml",
    rules_path: str | Path = "config/routing_rules.yaml",
) -> tuple[dict[str, ProviderConfig], dict[str, RoutingRule]]:
    """Load and cross-validate provider registry and routing rules."""

    providers = load_provider_registry(registry_path)
    rules = load_routing_rules(rules_path)

    for rule in rules.values():
        for ref in [*rule.prefer, *rule.fallback_order]:
            provider_id, model = split_provider_ref(ref, providers)
            if provider_id not in providers:
                continue
            _validate_model_ref(providers[provider_id], model, ref)

    return providers, rules


def validate_route_consistency(
    providers: dict[str, ProviderConfig],
    rules: dict[str, RoutingRule],
) -> list[str]:
    """Return config consistency issues for impossible preferred routes."""

    issues: list[str] = []
    issues.extend(validate_task_safety(rules))
    for provider in providers.values():
        if provider.fallback_provider and provider.fallback_provider not in providers:
            issues.append(
                f"provider {provider.provider_id}: fallback_provider {provider.fallback_provider} is not registered"
            )
    for rule in rules.values():
        required = set(rule.required_capabilities)
        if not required:
            continue
        viable = []
        for ref in rule.prefer:
            provider_id, _model = split_provider_ref(ref, providers)
            provider = providers.get(provider_id)
            if not provider:
                issues.append(f"{rule.task_type}: preferred provider {ref} is not registered")
                continue
            if not provider.enabled:
                continue
            if not provider.supports_capabilities(required):
                missing = sorted(required.difference(provider.capabilities))
                issues.append(
                    f"{rule.task_type}: preferred provider {ref} missing capabilities: {', '.join(missing)}"
                )
                continue
            if rule.max_cost_tier and COST_TIERS[provider.cost_tier] > COST_TIERS[rule.max_cost_tier]:
                issues.append(
                    f"{rule.task_type}: preferred provider {ref} cost tier {provider.cost_tier} "
                    f"exceeds rule max {rule.max_cost_tier}"
                )
                continue
            viable.append(ref)
        if not viable:
            issues.append(f"{rule.task_type}: no preferred provider can satisfy required capabilities and cost")
    return issues


def validate_task_safety(rules: dict[str, RoutingRule]) -> list[str]:
    """Return deterministic lint issues for dangerous task names missing required capabilities."""

    expectations: list[tuple[tuple[str, ...], tuple[set[str], ...], str]] = [
        (
            ("code_edit", "edit", "write", "patch", "refactor", "modify"),
            ({"repo_edit"}, {"local_file_access", "filesystem"}),
            "repo_edit and local_file_access/filesystem",
        ),
        (
            ("test_runner", "run_tests", "test"),
            ({"test_runner", "terminal"},),
            "test_runner or terminal",
        ),
        (
            ("shell", "terminal", "command", "exec", "run_command"),
            ({"terminal"},),
            "terminal",
        ),
        (
            ("memory_sensitive", "local_sensitive", "secret", "credential"),
            ({"local_sensitive", "local_file_access"},),
            "local_sensitive or local_file_access",
        ),
        (
            ("browser", "network", "http", "fetch", "url", "send_message", "mcp"),
            ({"mcp_tools"},),
            "mcp_tools",
        ),
    ]
    issues: list[str] = []
    for rule in rules.values():
        normalized = rule.task_type.lower()
        required = set(rule.required_capabilities)
        for patterns, required_any_sets, description in expectations:
            if not any(pattern in normalized for pattern in patterns):
                continue
            for required_any in required_any_sets:
                if required.isdisjoint(required_any):
                    issues.append(
                        f"{rule.task_type}: suspicious task type missing required capability: {description}"
                    )
                    break
            break
    return issues


def split_provider_ref(ref: str, providers: dict[str, ProviderConfig]) -> tuple[str, str | None]:
    """Resolve provider refs like openrouter.claude_opus into provider/model alias."""

    if ref in providers:
        return ref, None
    prefix, sep, suffix = ref.partition(".")
    if sep and prefix in providers:
        return prefix, suffix
    return ref, None


def validate_provider_model_ref(ref: str, providers: dict[str, ProviderConfig]) -> tuple[str, str | None]:
    """Resolve and validate a provider.model reference."""

    provider_id, model = split_provider_ref(ref, providers)
    if provider_id not in providers:
        raise ConfigError(f"unknown provider reference {ref!r}")
    _validate_model_ref(providers[provider_id], model, ref)
    return provider_id, model


def _strict_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{field} must be a YAML boolean true/false, not {value!r}")


def _optional_strict_bool(value: Any, field: str) -> bool | None:
    if value is None:
        return None
    return _strict_bool(value, field)


def _validate_model_ref(provider: ProviderConfig, model: str | None, ref: str) -> None:
    if model is None:
        return
    aliases = provider.metadata.get("model_aliases", {})
    if model in aliases or model in provider.available_models:
        return
    raise ConfigError(f"provider reference {ref!r} uses unknown model alias or model {model!r}")


def _validate_local_base_url(
    provider_id: str,
    base_url: str | None,
    *,
    local_trust_boundary: str = "private_network",
    allowed_hosts: Any = None,
) -> None:
    if not base_url:
        raise ConfigError(f"provider {provider_id!r} has allow_cloud=false but no base_url")
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname
    if not host:
        raise ConfigError(f"provider {provider_id!r} has invalid base_url {base_url!r}")
    lowered = _normalize_host(host)
    if local_trust_boundary == "explicit_allowlist":
        allowed = {_normalize_host(str(item)) for item in (allowed_hosts or [])}
        if lowered in allowed:
            return
        raise ConfigError(
            f"provider {provider_id!r} has allow_cloud=false but base_url host {host!r} is not in allowed_hosts"
        )
    if lowered == "localhost":
        return
    if local_trust_boundary == "private_network" and lowered.endswith(".local"):
        return
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError as exc:
        raise ConfigError(
            f"provider {provider_id!r} has allow_cloud=false but base_url host {host!r} is not local/private"
        ) from exc
    if local_trust_boundary == "loopback_only" and address.is_loopback:
        return
    if local_trust_boundary == "private_network" and (address.is_loopback or address.is_private):
        return
    raise ConfigError(
        f"provider {provider_id!r} has allow_cloud=false but base_url host {host!r} is outside {local_trust_boundary}"
    )


def _validate_http_base_url_scheme(provider_id: str, base_url: str) -> None:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ConfigError(
            f"provider {provider_id!r} has unsupported base_url scheme {parsed.scheme!r}; expected http or https"
        )


def _normalize_host(host: str) -> str:
    return host.rstrip(".").encode("idna").decode("ascii").lower()


_PROVIDER_FIELDS = {
    "enabled",
    "type",
    "provider_type",
    "base_url",
    "api_key_env",
    "default_model",
    "available_models",
    "capabilities",
    "priority",
    "cost_tier",
    "latency_tier",
    "context_window",
    "health_check_endpoint",
    "fallback_provider",
    "allow_cloud",
    "local_trust_boundary",
    "allowed_hosts",
    "requires_auth",
}
