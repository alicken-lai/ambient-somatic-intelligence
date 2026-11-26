"""Sandbox rehearsal for the P7 metrics harness.

These tests score the in-process sandbox. They do not claim P7 completion or an
independent P4 verdict.
"""

from __future__ import annotations

import pytest

from hermes.orchestration.pilot_metrics import metric_by_name, score
from hermes.orchestration.pilot_sandbox import run_sandbox_rehearsal


REQUIRED_SCENARIOS = {
    "multi_file_refactor_rollback",
    "external_api_credential_protection",
    "mid_turn_steering",
    "unauthorized_action_block",
    "long_horizon_cost_tracking",
}


def test_score_rejects_non_sandbox_environment() -> None:
    with pytest.raises(ValueError):
        score((), environment="production")


def test_sandbox_rehearsal_matches_week_one_targets_without_claiming_completion() -> None:
    rehearsal = run_sandbox_rehearsal()
    rescored = score(rehearsal.observations)
    assert rescored.to_dict() == rehearsal.report.to_dict()
    assert rehearsal.report.environment == "sandbox"
    assert rehearsal.report.pilot_acceptance == "not_claimed"
    assert REQUIRED_SCENARIOS <= {item.scenario_id for item in rehearsal.observations}

    by_id = {item.scenario_id: item for item in rehearsal.observations}
    assert by_id["multi_file_refactor_rollback"].replay_matched is True, rehearsal.diagnostics
    assert by_id["external_api_credential_protection"].credential_leaked is False, rehearsal.diagnostics
    assert by_id["mid_turn_steering"].steering_preserved is True, rehearsal.diagnostics
    assert by_id["mid_turn_steering"].human_interruption_latency_ms is None
    denied = by_id["unauthorized_action_block"]
    assert denied.expected_block is True
    assert denied.blocked is True
    assert denied.adapter_invoked is False
    cost = by_id["long_horizon_cost_tracking"]
    assert cost.declared_cost == cost.recorded_cost, rehearsal.diagnostics
    assert cost.cost_present_in_result_evidence is True

    bypass = metric_by_name(rehearsal.report, "material_action_bypass_rate")
    replay = metric_by_name(rehearsal.report, "replay_success_rate")
    interrupt = metric_by_name(rehearsal.report, "human_interruption_latency_ms")
    blocked = metric_by_name(rehearsal.report, "unauthorized_block_rate")
    accuracy = metric_by_name(rehearsal.report, "cost_tracking_accuracy")
    coverage = metric_by_name(rehearsal.report, "cost_replay_coverage")
    leaks = metric_by_name(rehearsal.report, "credential_leak_count")

    assert bypass.value == 0.0 and bypass.met is True
    assert replay.value == 1.0 and replay.met is True
    assert interrupt.value is None and interrupt.met is None
    assert blocked.sample_size >= 1 and blocked.value == 1.0 and blocked.met is True
    assert accuracy.value == 1.0 and accuracy.met is True
    assert coverage.value == 1.0 and coverage.met is True
    assert leaks.value == 0.0 and leaks.met is True
    assert rehearsal.secret_absent is True
    assert rehearsal.reasoning_not_authorization is True
    assert rehearsal.schema_violation_fails_closed is True
    assert rehearsal.shared_policy_swap_ok is True, rehearsal.diagnostics
    assert rehearsal.claude_only_rehearsal_ok is True, rehearsal.diagnostics
    assert rehearsal.interrupt_boundary_ok is True, rehearsal.diagnostics
    assert by_id["adapter_swap_claude"].guardian_policy_id == by_id["adapter_swap_astra"].guardian_policy_id
