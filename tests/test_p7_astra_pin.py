"""Pinned Astra target and the no-credential canary stop."""

from __future__ import annotations

import pytest

from hermes.orchestration.astra_pilot import (
    CANARY_BLOCKED_NO_CREDENTIAL,
    PINNED_BASE_URL,
    PINNED_MODEL_ID,
    FakeAstraAdapter,
    canary_probe,
)
from hermes.orchestration.models import ProviderConfig


def test_operator_pin_is_recorded() -> None:
    assert PINNED_MODEL_ID == "gpt-6.2-astra"
    assert PINNED_BASE_URL == "https://api.teamorouter.com/v1"


def test_local_astra_still_refuses_network_configuration() -> None:
    with pytest.raises(RuntimeError):
        FakeAstraAdapter(
            ProviderConfig(
                provider_id="astra-sandbox",
                enabled=True,
                provider_type="sandbox",
                base_url=PINNED_BASE_URL,
                default_model=PINNED_MODEL_ID,
                capabilities=["general_reasoning"],
                allow_cloud=False,
                requires_auth=False,
            )
        )


def test_canary_without_credential_does_not_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEAMOROUTER_API_KEY", raising=False)

    def _fail(*_args, **_kwargs):
        raise AssertionError("canary opened a socket without a credential")

    monkeypatch.setattr("hermes.orchestration.astra_pilot.urllib.request.urlopen", _fail)
    result = canary_probe()
    assert result["status"] == CANARY_BLOCKED_NO_CREDENTIAL
    assert result["called"] is False
    assert "key" not in result
    assert result["model"] == PINNED_MODEL_ID
