"""Single vs deliberation A/B evaluation runner."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from hermes.deliberation.evaluation.golden_traces import GoldenTrace
from hermes.deliberation.evaluation.metrics import calculate_metrics
from hermes.deliberation.evaluation.scorecard import generate_scorecard
from hermes.deliberation.layer import run_deliberation


MODES = ["single", "light", "full"]


def run_ab_test(trace: GoldenTrace, *, trace_dir: str | Path = "logs/deliberation_eval") -> dict[str, Any]:
    mode_results: dict[str, dict[str, Any]] = {}
    metrics: dict[str, dict[str, Any]] = {}
    scorecards: dict[str, dict[str, Any]] = {}
    for mode in MODES:
        result = run_deliberation(
            trace.task,
            mode=mode,  # type: ignore[arg-type]
            context={"trace_dir": trace_dir, "no_save_trace": True, "evidence": _expected_evidence(trace)},
        ).to_dict()
        mode_results[mode] = result
        metrics[mode] = calculate_metrics(result)
        scorecards[mode] = generate_scorecard(trace.id, result).to_dict()
    winner = max(MODES, key=lambda mode: scorecards[mode]["overall_score"])
    return {
        "task_id": trace.id,
        "category": trace.category,
        "winner": winner,
        "reason": _reason(winner, scorecards, metrics),
        "metrics": metrics,
        "scorecards": scorecards,
        "guardian_expected": trace.expected_guardian_trigger,
    }


def run_ab_suite(
    traces: list[GoldenTrace],
    *,
    output_path: str | Path = "reports/deliberation_ab_results.json",
) -> list[dict[str, Any]]:
    results = [run_ab_test(trace) for trace in traces]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    return results


def _expected_evidence(trace: GoldenTrace) -> dict[str, bool]:
    return {item.lower(): True for item in trace.expected_verifications}


def _reason(winner: str, scorecards: dict[str, dict[str, Any]], metrics: dict[str, dict[str, Any]]) -> str:
    card = scorecards[winner]
    metric = metrics[winner]
    return (
        f"{winner} had the highest overall score ({card['overall_score']}) with "
        f"verification coverage {metric['verification_coverage']} and "
        f"hallucination risk {metric['hallucination_risk_score']}."
    )
