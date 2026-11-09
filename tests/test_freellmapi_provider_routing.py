"""Offline FreeLLMAPI source configuration/routing tests, never live probes."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from hermes.orchestration.adapters import OpenAICompatibleAdapter, ProviderAdapter
from hermes.orchestration.config_loader import load_orchestration_config, validate_route_consistency
from hermes.orchestration.guardian import GuardianDecision, StaticGuardian
from hermes.orchestration.health import ProviderHealthChecker
from hermes.orchestration.models import HermesResponse, ProviderRequest, RoutePolicy
from hermes.orchestration.routing import RoutingEngine


ROOT = Path(__file__).resolve().parents[1]
DIRECT_PAID_IDS = {"openrouter", "teamorouter"}


class _SyntheticAdapter(ProviderAdapter):
    def __init__(self, config, calls, fail=False):
        super().__init__(config)
        self.calls, self.fail = calls, fail

    def health_check(self, timeout_seconds=2.0):
        return True, "synthetic"

    def invoke(self, request, model=None):
        self.calls.append(self.name)
        return HermesResponse(provider=self.name, model=model or self.config.default_model,
                              status="error" if self.fail else "success", content="synthetic")

    def normalize_response(self, response, latency_ms, model):
        raise AssertionError("not used by synthetic routing adapter")


class _SyntheticHTTP:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self):
        return json.dumps({"choices": [{"message": {"content": "synthetic reply"}}]}).encode()


class FreeLLMAPIProviderTests(unittest.TestCase):
    def setUp(self):
        self.providers, self.rules = load_orchestration_config(
            ROOT / "config/provider_registry.yaml", ROOT / "config/routing_rules.yaml")
        self.free = self.providers["freellmapi"]

    def engine(self, *, failed=()):
        calls = []
        adapters = {name: _SyntheticAdapter(cfg, calls, fail=name in failed)
                    for name, cfg in self.providers.items()}
        engine = RoutingEngine(self.providers, self.rules, adapters=adapters,
            health_checker=ProviderHealthChecker({name: (True, "synthetic") for name in self.providers}),
            guardian_checker=StaticGuardian(GuardianDecision.ALLOW, reason="synthetic permission only"))
        return engine, calls

    def test_default_config_consistency(self):
        self.assertEqual(validate_route_consistency(self.providers, self.rules), [])

    def test_exact_bridge_auto_and_required_env_reference(self):
        self.assertTrue(self.free.enabled)
        self.assertEqual(self.free.provider_type, "openai-compatible")
        self.assertEqual(self.free.base_url, "http://127.0.0.1:31415/v1")
        self.assertEqual(self.free.default_model, "auto")
        self.assertEqual(self.free.available_models, ["auto"])
        self.assertEqual(self.free.api_key_env, "OPENAI_API_KEY")
        self.assertTrue(self.free.requires_auth)

    def test_loopback_forwarder_still_cloud_without_privileged_capabilities(self):
        self.assertTrue(self.free.allow_cloud)
        self.assertTrue(set(self.free.capabilities).isdisjoint(
            {"local_sensitive", "local_file_access", "filesystem", "repo_edit", "terminal", "test_runner", "mcp_tools"}))
        self.assertIsNone(self.free.context_window)
        self.assertNotIn("long_context", self.free.capabilities)

    def test_direct_paid_providers_disabled_but_original_model_configs_preserved(self):
        for name in DIRECT_PAID_IDS:
            cfg = self.providers[name]
            self.assertFalse(cfg.enabled)
            self.assertTrue(cfg.base_url)
            self.assertTrue(cfg.default_model)
            self.assertTrue(cfg.available_models)
            self.assertTrue(cfg.metadata.get("model_aliases"))

    def test_no_direct_paid_reference_in_any_route_or_provider_fallback(self):
        refs = [p.fallback_provider for p in self.providers.values() if p.fallback_provider]
        refs += [ref for rule in self.rules.values() for ref in [*rule.prefer, *rule.fallback_order]]
        self.assertFalse({ref.split(".", 1)[0] for ref in refs} & DIRECT_PAID_IDS)

    def test_openai_compatible_urls_keep_exact_v1_path(self):
        adapter = OpenAICompatibleAdapter(self.free)
        self.assertEqual(adapter.chat_completions_url(), "http://127.0.0.1:31415/v1/chat/completions")
        self.assertEqual(adapter.models_url(), "http://127.0.0.1:31415/v1/models")
        self.assertEqual(adapter.health_url(), "http://127.0.0.1:31415/v1/models")

    def test_missing_key_fails_before_http(self):
        with patch.dict(os.environ, {}, clear=True), patch("urllib.request.urlopen") as http:
            response = OpenAICompatibleAdapter(self.free).invoke(ProviderRequest("general_reasoning", "synthetic"))
            healthy, _ = OpenAICompatibleAdapter(self.free).health_check()
        self.assertEqual(response.error["category"], "missing_credentials")
        self.assertFalse(healthy)
        http.assert_not_called()

    def test_synthetic_http_formats_auto_and_auth_without_secret_in_result(self):
        marker = "SYNTHETIC_NOT_A_REAL_CREDENTIAL"
        with patch.dict(os.environ, {"OPENAI_API_KEY": marker}, clear=True), \
                patch("urllib.request.urlopen", return_value=_SyntheticHTTP()) as http:
            response = OpenAICompatibleAdapter(self.free).invoke(ProviderRequest("general_reasoning", "public synthetic"))
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:31415/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer " + marker)
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "auto")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "public synthetic"}])
        self.assertEqual(response.status, "success")
        self.assertNotIn(marker, json.dumps(response.to_dict()))

    def test_general_route_selects_free_bridge_without_paid_invocation(self):
        engine, calls = self.engine()
        response = engine.route(ProviderRequest("general_reasoning", "synthetic"))
        self.assertEqual(response.provider, "freellmapi")
        self.assertEqual(response.model, "auto")
        self.assertEqual(calls, ["freellmapi"])

    def test_bridge_failure_never_invokes_disabled_direct_paid_providers(self):
        engine, calls = self.engine(failed=set(self.providers))
        response = engine.route(ProviderRequest("general_reasoning", "synthetic"))
        self.assertEqual(response.status, "error")
        self.assertTrue(calls)
        self.assertFalse(set(calls) & DIRECT_PAID_IDS)

    def test_free_error_can_use_existing_nonpaid_direct_local_alternative(self):
        engine, calls = self.engine(failed={"freellmapi", "copilot"})
        response = engine.route(ProviderRequest("general_reasoning", "synthetic"))
        self.assertEqual(response.provider, "local_ollama_worker")
        self.assertFalse(set(calls) & DIRECT_PAID_IDS)

    def test_memory_sensitive_route_excludes_bridge_even_if_preferred(self):
        engine, calls = self.engine()
        response = engine.route(ProviderRequest("memory_sensitive_task", "synthetic private marker",
            policy=RoutePolicy(preferred_provider="freellmapi")))
        self.assertEqual(response.provider, "local_ollama_worker")
        self.assertNotIn("freellmapi", calls)
        self.assertFalse(set(calls) & DIRECT_PAID_IDS)

    def test_request_disallow_cloud_excludes_bridge(self):
        engine, calls = self.engine()
        response = engine.route(ProviderRequest("general_reasoning", "synthetic",
            policy=RoutePolicy(allow_cloud=False, preferred_provider="freellmapi")))
        self.assertEqual(response.provider, "local_ollama_worker")
        self.assertNotIn("freellmapi", calls)

    def test_strict_bridge_lock_on_sensitive_route_fails_closed(self):
        engine, calls = self.engine()
        response = engine.route(ProviderRequest("memory_sensitive_task", "synthetic",
            policy=RoutePolicy(preferred_provider="freellmapi", require_preferred_provider=True)))
        self.assertEqual(response.status, "error")
        self.assertEqual(calls, [])

    def test_private_route_cloud_false_remains_enforced(self):
        for task in ("memory_sensitive_task", "local_file_operation", "test_runner"):
            self.assertIs(self.rules[task].allow_cloud, False)


if __name__ == "__main__":
    unittest.main()
