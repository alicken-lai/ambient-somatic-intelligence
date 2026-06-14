#!/usr/bin/env python3
"""Hermes-ASI provider routing CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes.orchestration import ProviderRequest, RoutePolicy, RoutingEngine, load_orchestration_config
from hermes.orchestration.audit import JsonlAuditSink
from hermes.orchestration.config_loader import validate_route_consistency
from hermes.orchestration.health import ProviderHealthChecker
from hermes.deliberation import run_deliberation
from hermes.deliberation.evaluation.ab_test import run_ab_suite
from hermes.deliberation.evaluation.golden_traces import load_golden_traces
from hermes.deliberation.evaluation.knowledge_reports import (
    generate_failure_report,
    generate_playbook_report,
    generate_skill_report,
)
from hermes.deliberation.evaluation.learning_report import generate_learning_report
from hermes.deliberation.evaluation.report import generate_quality_report
from hermes.deliberation.memory import DeliberationEffectivenessMemory
from hermes.deliberation.roi import ROICalculator
from hermes.deliberation.strategy_engine import DeliberationStrategyEngine
from hermes.verification.reports import (
    generate_claim_report,
    generate_contradiction_report,
    generate_evidence_report,
    generate_verification_report,
)
from hermes.acquisition.reports import (
    generate_acquisition_report,
    generate_evidence_quality_report,
    generate_knowledge_index_report,
)
from hermes.calibration.reports import (
    generate_drift_report,
    generate_knowledge_health_report,
    generate_trust_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes-ASI provider orchestration CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    route = sub.add_parser("route", help="Select and optionally invoke a provider for a task.")
    route.add_argument("--task", help="Task type, e.g. code_edit or architecture_design.")
    route.add_argument("--prompt", help="User prompt to route.")
    route.add_argument("--registry", default="config/provider_registry.yaml")
    route.add_argument("--rules", default="config/routing_rules.yaml")
    route.add_argument("--capability", action="append", default=[], help="Additional required capability.")
    route.add_argument("--preferred-provider")
    route.add_argument("--require-preferred-provider", action="store_true")
    route.add_argument("--no-fallback", action="store_true")
    route.add_argument("--max-cost-tier", default="high", choices=["low", "medium", "high"])
    route.add_argument("--disallow-cloud", action="store_true")
    route.add_argument("--allow-local-file-access", action="store_true")
    route.add_argument("--allow-code-modification", action="store_true")
    route.add_argument("--allow-terminal-execution", action="store_true")
    route.add_argument("--allow-mcp-tools", action="store_true")
    route.add_argument("--validate-config", action="store_true", help="Validate registry/routing consistency and exit.")
    route.add_argument("--invoke", action="store_true", help="Actually call the selected provider.")
    route.add_argument("--check-health", action="store_true", help="In dry-run mode, perform real provider health checks.")
    route.add_argument("--audit-log", help="Append sanitized routing audit events to a JSONL file.")
    route.add_argument("--json", action="store_true", help="Print only JSON.")

    deliberate = sub.add_parser("deliberate", help="Run ASI Deliberation Layer for a task.")
    deliberate.add_argument("task")
    deliberate.add_argument("--mode", default="light", choices=["single", "light", "full", "guardian_required"])
    deliberate.add_argument("--dry-run", action="store_true")
    deliberate.add_argument("--show-trace", action="store_true")
    deliberate.add_argument("--providers", help="Comma-separated provider allowlist for trace metadata.")
    deliberate.add_argument("--no-save-trace", action="store_true")
    deliberate.add_argument("--registry", default="config/provider_registry.yaml")
    deliberate.add_argument("--config", default="config/deliberation.yaml")
    deliberate.add_argument("--json", action="store_true", help="Print only JSON.")

    report = sub.add_parser("deliberate-report", help="Evaluate golden traces and write quality report.")
    report.add_argument("--benchmarks", default="tests/golden_traces/benchmarks.json")
    report.add_argument("--output", default="reports/deliberation_quality_report.md")
    report.add_argument("--json", action="store_true", help="Print only JSON.")

    routing_report = sub.add_parser("routing-report", help="Generate adaptive routing learning report.")
    routing_report.add_argument("--benchmarks", default="tests/golden_traces/benchmarks.json")
    routing_report.add_argument("--output", default="reports/deliberation_learning_report.md")
    routing_report.add_argument("--json", action="store_true", help="Print only JSON.")

    roi_report = sub.add_parser("roi-report", help="Generate ROI and effectiveness summary JSON.")
    roi_report.add_argument("--benchmarks", default="tests/golden_traces/benchmarks.json")
    roi_report.add_argument("--output", default="reports/deliberation_roi_report.md")
    roi_report.add_argument("--json-output", default="reports/deliberation_roi_report.json")
    roi_report.add_argument("--json", action="store_true", help="Print only JSON.")

    strategy_report = sub.add_parser("strategy-report", help="Explain adaptive strategy for a task.")
    strategy_report.add_argument("task")
    strategy_report.add_argument("--task-class", default="architecture")
    strategy_report.add_argument("--risk-level", default="normal", choices=["normal", "high"])
    strategy_report.add_argument("--output", default="reports/deliberation_strategy_report.md")
    strategy_report.add_argument("--json-output", default="reports/deliberation_strategy_report.json")
    strategy_report.add_argument("--json", action="store_true", help="Print only JSON.")

    playbook_report = sub.add_parser("playbook-report", help="Generate deliberation playbook report.")
    playbook_report.add_argument("--output", default="reports/playbook_report.md")
    playbook_report.add_argument("--json", action="store_true", help="Print only JSON.")

    skill_report = sub.add_parser("skill-report", help="Generate deliberation skill report.")
    skill_report.add_argument("--output", default="reports/skill_report.md")
    skill_report.add_argument("--json", action="store_true", help="Print only JSON.")

    failure_report = sub.add_parser("failure-report", help="Generate deliberation failure learning report.")
    failure_report.add_argument("--output", default="reports/failure_learning_report.md")
    failure_report.add_argument("--json", action="store_true", help="Print only JSON.")

    evidence_report = sub.add_parser("evidence-report", help="Generate evidence quality report.")
    evidence_report.add_argument("--output", default="reports/evidence_report.md")
    evidence_report.add_argument("--json", action="store_true", help="Print only JSON.")

    claim_report = sub.add_parser("claim-report", help="Generate claim registry report.")
    claim_report.add_argument("--output", default="reports/claim_report.md")
    claim_report.add_argument("--json", action="store_true", help="Print only JSON.")

    verification_report = sub.add_parser("verification-report", help="Generate verification coverage report.")
    verification_report.add_argument("--output", default="reports/verification_report.md")
    verification_report.add_argument("--json", action="store_true", help="Print only JSON.")

    contradiction_report = sub.add_parser("contradiction-report", help="Generate contradiction report.")
    contradiction_report.add_argument("--output", default="reports/contradiction_report.md")
    contradiction_report.add_argument("--json", action="store_true", help="Print only JSON.")

    acquisition_report = sub.add_parser("acquisition-report", help="Generate evidence acquisition report.")
    acquisition_report.add_argument("--output", default="reports/acquisition_report.md")
    acquisition_report.add_argument("--json", action="store_true", help="Print only JSON.")

    evidence_quality_report = sub.add_parser("evidence-quality-report", help="Generate evidence quality acquisition report.")
    evidence_quality_report.add_argument("--output", default="reports/evidence_quality_report.md")
    evidence_quality_report.add_argument("--json", action="store_true", help="Print only JSON.")

    knowledge_index_report = sub.add_parser("knowledge-index-report", help="Generate internal knowledge index report.")
    knowledge_index_report.add_argument("--output", default="reports/knowledge_index_report.md")
    knowledge_index_report.add_argument("--json", action="store_true", help="Print only JSON.")

    knowledge_health_report = sub.add_parser("knowledge-health-report", help="Generate calibrated knowledge health report.")
    knowledge_health_report.add_argument("--output", default="reports/knowledge_health_report.md")
    knowledge_health_report.add_argument("--json", action="store_true", help="Print only JSON.")

    trust_report = sub.add_parser("trust-report", help="Generate trust calibration report.")
    trust_report.add_argument("--output", default="reports/trust_report.md")
    trust_report.add_argument("--json", action="store_true", help="Print only JSON.")

    drift_report = sub.add_parser("drift-report", help="Generate knowledge drift report.")
    drift_report.add_argument("--output", default="reports/drift_report.md")
    drift_report.add_argument("--json", action="store_true", help="Print only JSON.")
    return parser


def route_command(args: argparse.Namespace) -> int:
    providers, rules = load_orchestration_config(args.registry, args.rules)
    config_warnings = validate_route_consistency(providers, rules)
    if args.validate_config:
        issues = config_warnings
        if args.json:
            print(json.dumps({"issues": issues}, indent=2, ensure_ascii=False))
        else:
            if issues:
                for issue in issues:
                    print(issue)
            else:
                print("No route consistency issues found.")
        return 1 if issues else 0
    if not args.task or not args.prompt:
        raise SystemExit("--task and --prompt are required unless --validate-config is used")
    policy = RoutePolicy(
        allow_cloud=not args.disallow_cloud,
        allow_local_file_access=args.allow_local_file_access,
        allow_code_modification=args.allow_code_modification,
        allow_terminal_execution=args.allow_terminal_execution,
        allow_mcp_tools=args.allow_mcp_tools,
        max_cost_tier=args.max_cost_tier,
        preferred_provider=args.preferred_provider,
        require_preferred_provider=args.require_preferred_provider,
        no_fallback=args.no_fallback,
    )
    request = ProviderRequest(
        task_type=args.task,
        prompt=args.prompt,
        required_capabilities=args.capability,
        policy=policy,
    )
    health = ProviderHealthChecker(
        {
            provider_id: (True, "dry-run")
            for provider_id in providers
        }
    ) if not args.invoke and not args.check_health else None
    engine = RoutingEngine(
        providers,
        rules,
        health_checker=health,
        audit_sink=JsonlAuditSink(args.audit_log) if args.audit_log else None,
    )
    response = engine.route(request, dry_run=not args.invoke, check_health=args.check_health)
    if config_warnings:
        response.logs = [*response.logs, *[f"config_warning: {warning}" for warning in config_warnings]]
        if response.audit is not None:
            response.audit["config_warnings"] = config_warnings
    payload = response.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Selected provider: {payload['provider']}")
        print(f"Model: {payload['model']}")
        fallback = payload.get("fallback") or {}
        attempts = fallback.get("attempts") or []
        fallback_label = fallback.get("planned_fallback_provider")
        if not fallback_label and attempts:
            fallback_label = attempts[-1]["provider"]
        print(f"Fallback: {fallback_label or 'none'}")
        print(f"Reason: {'; '.join(payload['logs'])}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if response.status in {"success", "fallback"} else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "route":
        return route_command(args)
    if args.command == "deliberate":
        return deliberate_command(args)
    if args.command == "deliberate-report":
        return deliberate_report_command(args)
    if args.command == "routing-report":
        return routing_report_command(args)
    if args.command == "roi-report":
        return roi_report_command(args)
    if args.command == "strategy-report":
        return strategy_report_command(args)
    if args.command == "playbook-report":
        return knowledge_report_command(generate_playbook_report, args)
    if args.command == "skill-report":
        return knowledge_report_command(generate_skill_report, args)
    if args.command == "failure-report":
        return knowledge_report_command(generate_failure_report, args)
    if args.command == "evidence-report":
        return knowledge_report_command(generate_evidence_report, args)
    if args.command == "claim-report":
        return knowledge_report_command(generate_claim_report, args)
    if args.command == "verification-report":
        return knowledge_report_command(generate_verification_report, args)
    if args.command == "contradiction-report":
        return knowledge_report_command(generate_contradiction_report, args)
    if args.command == "acquisition-report":
        return knowledge_report_command(generate_acquisition_report, args)
    if args.command == "evidence-quality-report":
        return knowledge_report_command(generate_evidence_quality_report, args)
    if args.command == "knowledge-index-report":
        return knowledge_report_command(generate_knowledge_index_report, args)
    if args.command == "knowledge-health-report":
        return knowledge_report_command(generate_knowledge_health_report, args)
    if args.command == "trust-report":
        return knowledge_report_command(generate_trust_report, args)
    if args.command == "drift-report":
        return knowledge_report_command(generate_drift_report, args)
    parser.error(f"unknown command: {args.command}")
    return 2


def deliberate_command(args: argparse.Namespace) -> int:
    context = {
        "dry_run": args.dry_run,
        "no_save_trace": args.no_save_trace,
        "registry_path": args.registry,
        "config_path": args.config,
    }
    if args.providers:
        context["providers"] = [item.strip() for item in args.providers.split(",") if item.strip()]
    result = run_deliberation(args.task, mode=args.mode, context=context).to_dict()
    if not args.show_trace:
        result.pop("trace_path", None)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Mode: {result['mode']}")
        print(f"Trace: {result.get('trace_id')}")
        if args.show_trace and result.get("trace_path"):
            print(f"Trace path: {result['trace_path']}")
        print(result["final_answer"])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def deliberate_report_command(args: argparse.Namespace) -> int:
    payload = generate_quality_report(benchmark_path=args.benchmarks, output_path=args.output)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Report path: {payload['report_path']}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def routing_report_command(args: argparse.Namespace) -> int:
    payload = generate_learning_report(benchmark_path=args.benchmarks, output_path=args.output)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Report path: {payload['report_path']}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def roi_report_command(args: argparse.Namespace) -> int:
    traces = load_golden_traces(args.benchmarks)
    results = run_ab_suite(traces)
    records = DeliberationEffectivenessMemory().update_from_ab_results(results)
    calculator = ROICalculator()
    roi_records = []
    for task_class, record in records.items():
        for mode, score in {
            "light": record.avg_light_score,
            "full": record.avg_full_score,
        }.items():
            roi_records.append(
                calculator.calculate(
                    task_type=task_class,
                    mode=mode,
                    baseline_quality=record.avg_single_score,
                    mode_quality=score,
                    baseline_verification=0.0,
                    mode_verification=max(0.0, score - record.avg_single_score) / 100.0,
                ).to_dict()
            )
    payload = {"roi_records": roi_records, "effectiveness": {key: value.to_dict() for key, value in records.items()}}
    _write_json(args.json_output, payload)
    _write_roi_markdown(args.output, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def strategy_report_command(args: argparse.Namespace) -> int:
    historical = DeliberationEffectivenessMemory().get(args.task_class)
    payload = DeliberationStrategyEngine().plan(
        task=args.task,
        task_class=args.task_class,
        historical=historical,
        risk_level=args.risk_level,
    )
    _write_json(args.json_output, payload)
    _write_strategy_markdown(args.output, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def knowledge_report_command(generator, args: argparse.Namespace) -> int:
    payload = generator(output_path=args.output)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Report path: {payload['report_path']}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _write_json(path: str, payload: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_roi_markdown(path: str, payload: dict) -> None:
    lines = [
        "# Deliberation ROI Report",
        "",
        "## Effectiveness By Task Class",
        "",
        "| Task Class | Best Mode | Samples | Single | Light | Full | Avg ROI |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in payload["effectiveness"].values():
        lines.append(
            f"| {record['task_class']} | {record['best_mode']} | {record['sample_count']} | "
            f"{record['avg_single_score']:.2f} | {record['avg_light_score']:.2f} | "
            f"{record['avg_full_score']:.2f} | {record['avg_roi']:.2f} |"
        )
    lines.extend(["", "## ROI Records", ""])
    for record in payload["roi_records"]:
        lines.append(
            f"- {record['task_type']} / {record['mode']}: ROI {record['overall_roi']}, "
            f"quality gain {record['quality_gain']}, verification gain {record['verification_gain']}"
        )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_strategy_markdown(path: str, payload: dict) -> None:
    decision = payload["routing_decision"]
    lines = [
        "# Deliberation Strategy Report",
        "",
        f"Strategy: `{payload['strategy']}`",
        f"Selected mode: `{decision['selected_mode']}`",
        f"Confidence: {decision['confidence']}",
        f"Expected ROI: {payload['expected_roi']}",
        f"Verification depth: `{payload['verification_depth']}`",
        f"Guardian involvement: {payload['guardian_involvement']}",
        "",
        "## Routing Explainability",
        "",
        f"- Why not single: {decision['why_not_single']}",
        f"- Why not light: {decision['why_not_light']}",
        f"- Why not full: {decision['why_not_full']}",
        "",
        "## Selected Children",
        "",
    ]
    for child in payload["selected_children"]:
        lines.append(f"- {child['name']}: {', '.join(child['capabilities'])}")
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
