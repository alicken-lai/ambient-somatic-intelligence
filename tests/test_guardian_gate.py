from __future__ import annotations

import pytest

from hermes.deliberation import run_deliberation, triage_task


@pytest.mark.parametrize(
    ("task", "label"),
    [
        ("Append a DMN memory record after quality report generation", "memory_mutation"),
        ("Modify provider registry to enable cursor_cli", "state_changing"),
        ("Run a shell command that changes local state", "state_changing"),
        ("Write a new local file with deliberation results", "state_changing"),
        ("Deploy the deliberation dashboard", "state_changing"),
        ("Expose a report over the network", "state_changing"),
        ("Read and rotate a provider API key token", "credential_sensitive"),
        ("Perform a repository-wide refactor", "state_changing"),
        ("Delete old deliberation traces", "state_changing"),
    ],
)
def test_risky_tasks_trigger_guardian(task: str, label: str) -> None:
    triage = triage_task(task)
    assert label in triage.labels
    assert triage.guardian_required is True
    assert triage.route_mode == "guardian_required"


def test_guardian_required_result_preserves_warning() -> None:
    result = run_deliberation(
        "Modify provider registry to enable a CLI provider",
        mode="light",
        context={"no_save_trace": True},
    ).to_dict()
    assert result["mode"] == "guardian_required"
    assert result["guardian_warnings"] == ["Guardian required"]
    assert result["triage"]["guardian_required"] is True
