"""Markdown quality report generation for deliberation evaluation."""

from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Any

from hermes.deliberation.evaluation.ab_test import run_ab_suite
from hermes.deliberation.evaluation.golden_traces import load_golden_traces


def generate_quality_report(
    *,
    benchmark_path: str | Path = "tests/golden_traces/benchmarks.json",
    output_path: str | Path = "reports/deliberation_quality_report.md",
) -> dict[str, Any]:
    traces = load_golden_traces(benchmark_path)
    results = run_ab_suite(traces)
    mode_scores: dict[str, list[float]] = {"single": [], "light": [], "full": []}
    mode_wins = {"single": 0, "light": 0, "full": 0}
    safety_scores: list[float] = []
    verification_scores: list[float] = []
    for result in results:
        mode_wins[result["winner"]] += 1
        for mode, card in result["scorecards"].items():
            mode_scores[mode].append(float(card["overall_score"]))
            safety_scores.append(float(card["safety_score"]))
            verification_scores.append(float(card["verification_score"]))
    overall_quality = mean([score for scores in mode_scores.values() for score in scores]) if results else 0.0
    lines = [
        "# Deliberation Quality Report",
        "",
        f"Benchmarks evaluated: {len(results)}",
        f"Overall quality: {overall_quality:.2f}",
        f"Average safety score: {mean(safety_scores):.2f}" if safety_scores else "Average safety score: 0.00",
        f"Average verification score: {mean(verification_scores):.2f}" if verification_scores else "Average verification score: 0.00",
        "",
        "## Mode Comparison",
        "",
        "| Mode | Wins | Average Overall |",
        "| --- | ---: | ---: |",
    ]
    for mode, scores in mode_scores.items():
        avg = mean(scores) if scores else 0.0
        lines.append(f"| {mode} | {mode_wins[mode]} | {avg:.2f} |")
    lines.extend(
        [
            "",
            "## Failure Analysis",
            "",
            "- Unsupported claims remain the primary hallucination-risk proxy.",
            "- Guardian-required tasks are expected to preserve warnings instead of silently executing.",
            "- Trace completeness is scored independently from answer quality.",
            "",
            "## Recommendations",
            "",
            "- Increase verifier evidence sources before enabling real provider children.",
            "- Keep disabled CLI providers observable but non-invokable until explicitly configured.",
            "- Track scorecard trends across releases before promoting full deliberation as default.",
        ]
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "benchmark_count": len(results),
        "overall_quality": round(overall_quality, 2),
        "mode_wins": mode_wins,
        "report_path": str(path),
    }
