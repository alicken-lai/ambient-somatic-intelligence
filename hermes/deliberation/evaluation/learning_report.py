"""Learning report generation for adaptive deliberation routing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes.deliberation.evaluation.ab_test import run_ab_suite
from hermes.deliberation.evaluation.golden_traces import load_golden_traces
from hermes.deliberation.memory import DeliberationEffectivenessMemory
from hermes.deliberation.router import AdaptiveRoutingLearner


def generate_learning_report(
    *,
    benchmark_path: str | Path = "tests/golden_traces/benchmarks.json",
    output_path: str | Path = "reports/deliberation_learning_report.md",
) -> dict[str, Any]:
    traces = load_golden_traces(benchmark_path)
    ab_results = run_ab_suite(traces)
    memory = DeliberationEffectivenessMemory()
    records = memory.update_from_ab_results(ab_results)
    recommendations = AdaptiveRoutingLearner().learn_defaults(records)
    most_effective = sorted(records.values(), key=lambda record: max(record.avg_single_score, record.avg_light_score, record.avg_full_score), reverse=True)
    highest_roi = sorted(records.values(), key=lambda record: record.avg_roi, reverse=True)
    lines = [
        "# Deliberation Learning Report",
        "",
        "## Most Effective Modes",
        "",
        "| Task Class | Samples | Best Mode | Single | Light | Full | Avg ROI |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for record in most_effective:
        lines.append(
            f"| {record.task_class} | {record.sample_count} | {record.best_mode} | "
            f"{record.avg_single_score:.2f} | {record.avg_light_score:.2f} | {record.avg_full_score:.2f} | {record.avg_roi:.2f} |"
        )
    lines.extend(["", "## Highest ROI Task Classes", ""])
    for record in highest_roi[:5]:
        lines.append(f"- {record.task_class}: avg ROI {record.avg_roi:.2f}, best mode {record.best_mode}")
    lines.extend(["", "## Recommended Routing Changes", ""])
    if recommendations:
        for task_class, recommendation in recommendations.items():
            lines.append(
                f"- {task_class}: default `{recommendation['default_mode']}` "
                f"(confidence {recommendation['confidence']}) - {recommendation['reason']}"
            )
    else:
        lines.append("- No adaptive default changes met confidence and sample thresholds.")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "Adaptive routing may change mode selection, child selection, and verification depth. It may not change Guardian rules, provider permissions, credential access policies, memory write policies, or human approval requirements.",
        ]
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "benchmark_count": len(traces),
        "task_classes": len(records),
        "recommendation_count": len(recommendations),
        "report_path": str(path),
        "recommendations": recommendations,
    }
