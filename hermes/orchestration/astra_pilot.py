"""P7 pilot adapters.

PINNED_MODEL_ID and PINNED_BASE_URL are the operator-supplied canary target.
Local stand-ins still refuse base_url and api_key_env, so sandbox runs do not
open that URL. The canary helper reads TEAMOROUTER_API_KEY from the environment
and never returns the key.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from hermes.orchestration.adapters import ProviderAdapter
from hermes.orchestration.envelopes import ProposedActionEnvelope
from hermes.orchestration.models import HermesResponse, ProviderConfig, ProviderRequest


PINNED_MODEL_ID = "gpt-6.2-astra"
PINNED_BASE_URL = "https://api.teamorouter.com/v1"
CANARY_API_KEY_ENV = "TEAMOROUTER_API_KEY"
CANARY_BLOCKED_NO_CREDENTIAL = "CANARY_BLOCKED_NO_CREDENTIAL"


class LocalPilotAdapter(ProviderAdapter):
    """In-process adapter. Network configuration is refused."""

    proposed_by_label = "adapter:local-pilot"

    def __init__(self, config: ProviderConfig, *, tokens: int = 0, latency_ms: int = 0) -> None:
        if config.base_url or config.api_key_env:
            raise RuntimeError("local pilot adapter refuses network configuration")
        super().__init__(config)
        self.calls = 0
        self.tokens = tokens
        self.latency_ms_value = latency_ms
        self.executed_tool_ids: list[str] = []

    def health_check(self, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        return True, "local-pilot"

    def invoke(self, request: ProviderRequest, model: str | None = None) -> HermesResponse:
        self.calls += 1
        return HermesResponse(
            provider=self.name,
            model=PINNED_MODEL_ID,
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
        raise NotImplementedError("local pilot adapter does not accept provider payloads")

    def propose_action(self, context: dict[str, Any]) -> ProposedActionEnvelope:
        cleaned = dict(context)
        cleaned.pop("authorization_ref", None)
        cleaned["proposed_by"] = self.proposed_by_label
        return super().propose_action(cleaned)


class FakeAstraAdapter(LocalPilotAdapter):
    """Fake Astra. It is not the live Responses API."""

    proposed_by_label = "adapter:fake-astra"


class LocalClaudeAdapter(LocalPilotAdapter):
    """Local Claude-side stand-in used to rehearse rollback. It is not a live Claude API."""

    proposed_by_label = "adapter:claude-local"


def canary_probe(*, timeout_seconds: float = 20.0) -> dict[str, str | int | bool | None]:
    """One live call when the environment already holds the provider key.

    The returned record has no credential and no response body.
    """

    if not os.environ.get(CANARY_API_KEY_ENV):
        return {
            "status": CANARY_BLOCKED_NO_CREDENTIAL,
            "model": PINNED_MODEL_ID,
            "base_url": PINNED_BASE_URL,
            "http_status": None,
            "called": False,
        }
    key = os.environ[CANARY_API_KEY_ENV]
    url = PINNED_BASE_URL.rstrip("/") + "/responses"
    payload = json.dumps(
        {"model": PINNED_MODEL_ID, "input": "Reply with the single word pong."}
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response.read(1)
            http_status = int(response.status)
    except urllib.error.HTTPError as exc:
        return {
            "status": "CANARY_HTTP_ERROR",
            "model": PINNED_MODEL_ID,
            "base_url": PINNED_BASE_URL,
            "http_status": int(exc.code),
            "called": True,
        }
    except (OSError, urllib.error.URLError):
        return {
            "status": "CANARY_TRANSPORT_ERROR",
            "model": PINNED_MODEL_ID,
            "base_url": PINNED_BASE_URL,
            "http_status": None,
            "called": True,
        }
    ok = 200 <= http_status < 300
    return {
        "status": "CANARY_HTTP_OK" if ok else "CANARY_HTTP_ERROR",
        "model": PINNED_MODEL_ID,
        "base_url": PINNED_BASE_URL,
        "http_status": http_status,
        "called": True,
    }
