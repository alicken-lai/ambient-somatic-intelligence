"""ASI Deliberation Layer orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
import time
import uuid

import yaml

from hermes.deliberation.children import run_children
from hermes.deliberation.judge import judge_children
from hermes.deliberation.synthesizer import synthesize
from hermes.deliberation.trace import save_trace
from hermes.deliberation.triage import triage_task
from hermes.deliberation.verifier import verify_claims
from hermes.providers.cli_discovery import discover_from_registry

Mode = Literal["single", "light", "full", "guardian_required"]


@dataclass(frozen=True)
class DeliberationResult:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


def run_deliberation(
    task: str,
    mode: Mode = "light",
    context: dict[str, Any] | None = None,
) -> DeliberationResult:
    context = context or {}
    started = time.monotonic()
    config = _load_config(context.get("config_path", "config/deliberation.yaml"))
    trace_id = context.get("trace_id") or f"delib-{uuid.uuid4().hex[:12]}"
    triage = triage_task(task)
    selected_mode = triage.route_mode if mode == "light" and triage.route_mode != "single" else mode
    if selected_mode == "single" and triage.guardian_required:
        selected_mode = "guardian_required"
    guardian_required = selected_mode == "guardian_required" or triage.guardian_required

    providers = discover_from_registry(context.get("registry_path", "config/provider_registry.yaml"))
    max_children = int(config.get("deliberation", {}).get("max_children", 3))
    if selected_mode == "single":
        children: list[dict[str, Any]] = []
        judge = {
            "consensus": ["Single-provider mode selected; no jury used."],
            "disagreements": [],
            "unsupported_claims": [],
            "recommended_next_step": "single_answer",
        }
        verification: list[dict[str, str]] = []
    else:
        children_started = time.monotonic()
        children = run_children(task, mode=selected_mode, max_children=max_children)
        children_latency_ms = int((time.monotonic() - children_started) * 1000)
        judge_started = time.monotonic()
        judge = judge_children(children, guardian_required=guardian_required)
        judge_latency_ms = int((time.monotonic() - judge_started) * 1000)
        verifier_started = time.monotonic()
        verification = verify_claims(judge.get("unsupported_claims", []), context.get("evidence"))
        verifier_latency_ms = int((time.monotonic() - verifier_started) * 1000)
    if selected_mode == "single":
        children_latency_ms = 0
        judge_latency_ms = 0
        verifier_latency_ms = 0

    synthesizer_started = time.monotonic()
    result = synthesize(
        task=task,
        mode=selected_mode,
        children=children,
        judge=judge,
        verification=verification,
        trace_id=trace_id,
        guardian_required=guardian_required,
    )
    synthesizer_latency_ms = int((time.monotonic() - synthesizer_started) * 1000)
    total_latency_ms = int((time.monotonic() - started) * 1000)
    providers_used: list[str] = []
    trace = {
        "trace_id": trace_id,
        "task": task,
        "mode": selected_mode,
        "route_reason": triage.reason,
        "triage": triage.to_dict(),
        "providers_used": providers_used,
        "provider_discovery": providers,
        "children": children,
        "child_outputs": children,
        "judge": judge,
        "judge_output": judge,
        "verifier": verification,
        "verifier_output": verification,
        "synthesizer": result,
        "synthesizer_output": result,
        "guardian": {"required": guardian_required, "decision": "REVIEW_REQUIRED" if guardian_required else "NOT_REQUIRED"},
        "latency_ms": total_latency_ms,
        "children_latency_ms": children_latency_ms,
        "judge_latency_ms": judge_latency_ms,
        "verifier_latency_ms": verifier_latency_ms,
        "synthesizer_latency_ms": synthesizer_latency_ms,
        "errors": [],
        "selected_final_answer": result["final_answer"],
    }
    save_trace_enabled = bool(config.get("deliberation", {}).get("save_trace", True))
    if context.get("no_save_trace"):
        save_trace_enabled = False
    if save_trace_enabled:
        result["trace_path"] = str(save_trace(trace, trace_dir=context.get("trace_dir", "logs/deliberation")))
    result["triage"] = triage.to_dict()
    result["provider_discovery"] = providers
    result["providers_used"] = providers_used
    result["judge_output"] = judge
    result["latency_ms"] = total_latency_ms
    result["children_latency_ms"] = children_latency_ms
    result["judge_latency_ms"] = judge_latency_ms
    result["verifier_latency_ms"] = verifier_latency_ms
    result["synthesizer_latency_ms"] = synthesizer_latency_ms
    return DeliberationResult(result)


def _load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_file():
        return {"deliberation": {"max_children": 3, "save_trace": True}}
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
