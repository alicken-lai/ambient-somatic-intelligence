"""Reports for deliberation knowledge formation."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from hermes.deliberation.evaluation.ab_test import run_ab_suite
from hermes.deliberation.evaluation.golden_traces import load_golden_traces
from hermes.deliberation.failure_learning import learn_failures
from hermes.deliberation.pattern_mining import mine_patterns
from hermes.deliberation.playbooks import PlaybookRegistry
from hermes.deliberation.skills import SkillExtractor, SkillRegistry
from hermes.deliberation.skill_evolution import evaluate_skill_evolution


def build_knowledge_assets(benchmark_path: str | Path = "tests/golden_traces/benchmarks.json") -> dict[str, Any]:
    results = _load_or_run_ab_results(benchmark_path)
    skills = SkillExtractor().extract_from_ab_results(results)
    SkillRegistry().upsert_many(skills)
    playbooks = PlaybookRegistry().load()
    patterns = mine_patterns(results)
    evolution = evaluate_skill_evolution(skills)
    failures = learn_failures(results)
    return {
        "results": results,
        "skills": skills,
        "playbooks": playbooks,
        "patterns": patterns,
        "evolution": evolution,
        "failures": failures,
    }


def _load_or_run_ab_results(benchmark_path: str | Path) -> list[dict[str, Any]]:
    cached = Path("reports/deliberation_ab_results.json")
    if cached.is_file():
        raw = json.loads(cached.read_text(encoding="utf-8"))
        results = raw.get("results", [])
        if isinstance(results, list) and results:
            return results
    return run_ab_suite(load_golden_traces(benchmark_path))


def generate_playbook_report(output_path: str | Path = "reports/playbook_report.md") -> dict[str, Any]:
    assets = build_knowledge_assets()
    playbooks = list(assets["playbooks"].values())
    lines = [
        "# Playbook Report",
        "",
        "## Top Playbooks",
        "",
        "| Playbook | Task Types | Children | Verification | Guardian Requirements |",
        "| --- | --- | --- | --- | --- |",
    ]
    for playbook in playbooks:
        lines.append(
            f"| {playbook.name} | {', '.join(playbook.task_types)} | {', '.join(playbook.recommended_children)} | "
            f"{playbook.verification_depth} | {', '.join(playbook.guardian_requirements) or 'none'} |"
        )
    promoted = [item for item in assets["evolution"] if item["status"] == "promoted"]
    retired = [item for item in assets["evolution"] if item["status"] == "retired"]
    lines.extend(["", "## Promotion Candidates", ""])
    lines.extend([f"- {item['skill']}: {item['reason']}" for item in promoted] or ["- None"])
    lines.extend(["", "## Retirement Candidates", ""])
    lines.extend([f"- {item['skill']}: {item['reason']}" for item in retired] or ["- None"])
    return _write_report(output_path, lines, {"playbook_count": len(playbooks), "promotion_candidates": len(promoted), "retirement_candidates": len(retired)})


def generate_skill_report(output_path: str | Path = "reports/skill_report.md") -> dict[str, Any]:
    assets = build_knowledge_assets()
    skills = sorted(assets["skills"], key=lambda skill: (skill.average_roi, skill.average_score), reverse=True)
    evolution = assets["evolution"]
    lines = [
        "# Skill Report",
        "",
        "## Most Valuable Skills",
        "",
        "| Skill | Samples | Success Rate | Avg Score | Avg ROI |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for skill in skills:
        lines.append(f"| {skill.name} | {skill.sample_count} | {skill.success_rate:.2f} | {skill.average_score:.2f} | {skill.average_roi:.2f} |")
    lines.extend(["", "## Evolution", ""])
    for item in evolution:
        lines.append(f"- {item['skill']}: `{item['status']}` - {item['reason']}")
    lines.extend(["", "## Unused Skills", "", "- None detected in current benchmark-derived registry."])
    return _write_report(output_path, lines, {"skill_count": len(skills), "promoted": sum(1 for item in evolution if item["status"] == "promoted")})


def generate_failure_report(output_path: str | Path = "reports/failure_learning_report.md") -> dict[str, Any]:
    assets = build_knowledge_assets()
    failures = assets["failures"]
    lines = [
        "# Failure Learning Report",
        "",
        "## Top Failure Modes",
        "",
        "| Failure Type | Frequency | Root Cause | Recommended Fix |",
        "| --- | ---: | --- | --- |",
    ]
    for failure in failures:
        lines.append(f"| {failure['failure_type']} | {failure['frequency']} | {failure['root_cause']} | {failure['recommended_fix']} |")
    lines.extend(["", "## Recommended Governance Improvements", "", "- Keep learning advisory and preserve immutable Guardian boundaries."])
    return _write_report(output_path, lines, {"failure_mode_count": len(failures), "top_failure": failures[0]["failure_type"] if failures else None})


def _write_report(path: str | Path, lines: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**payload, "report_path": str(output), "json_path": str(json_path)}
