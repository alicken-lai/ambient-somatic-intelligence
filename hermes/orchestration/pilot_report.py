"""Render the in-process P7 sandbox metrics report.

The renderer does not call providers or open sockets. The text is a sandbox
record, not an independent review verdict.
"""

from __future__ import annotations

from hermes.orchestration.pilot_metrics import MetricValue
from hermes.orchestration.pilot_sandbox import SANDBOX_SECRET, run_sandbox_rehearsal


def render_sandbox_report() -> str:
    """Return the deterministic sandbox metrics report."""

    rehearsal = run_sandbox_rehearsal()
    report = rehearsal.report
    lines = [
        "# P7 沙盒度量報告",
        "",
        "**日期：** 2026-11-20",
        "**environment：** sandbox",
        "**pilot_acceptance：** not_claimed",
        "**REVIEW_STATUS：** AWAITING_INDEPENDENT_REVIEWER",
        "**IMPLEMENTER_VERDICT：** NONE",
        "",
        "這份文字由 `hermes.orchestration.pilot_report.render_sandbox_report` 從行程內沙盒產生。",
        "它記錄本機排練，不是現場 Astra 證據，也不是獨立驗證裁決。",
        "",
        "## 指標",
        "",
        "| 名稱 | 值 | 目標 | met | 樣本數 |",
        "|---|---|---|---|---:|",
    ]
    for metric in report.metrics:
        lines.append(
            "| `{name}` | {value} | {target} | {met} | {sample} |".format(
                name=metric.name,
                value=_cell(metric.value),
                target=_cell(metric.target),
                met=_met(metric),
                sample=metric.sample_size,
            )
        )
    lines.extend(
        [
            "",
            "## 情境",
            "",
        ]
    )
    for item in rehearsal.observations:
        lines.append(
            "- `{scenario}`: guardian={decision} adapter_invoked={invoked} "
            "replay_matched={replay} steering_preserved={steering}".format(
                scenario=item.scenario_id,
                decision=item.guardian_decision,
                invoked=str(item.adapter_invoked).lower(),
                replay=str(item.replay_matched).lower(),
                steering=_optional_bool(item.steering_preserved),
            )
        )
    lines.extend(
        [
            "",
            "## 沙盒旗標",
            "",
            f"- secret_absent: {str(rehearsal.secret_absent).lower()}",
            f"- reasoning_not_authorization: {str(rehearsal.reasoning_not_authorization).lower()}",
            f"- schema_violation_fails_closed: {str(rehearsal.schema_violation_fails_closed).lower()}",
            f"- shared_policy_swap_ok: {str(rehearsal.shared_policy_swap_ok).lower()}",
            f"- claude_only_rehearsal_ok: {str(rehearsal.claude_only_rehearsal_ok).lower()}",
            "",
            "## 尚未滿足的 P7 完成條件",
            "",
            "- 五個情境尚未對現場 Astra 執行。",
            "- human_interruption_latency_ms 維持 unobserved。路由耗時不算這項指標。",
            "- cost_replay_coverage 已記入沙盒結果證據。現場 Astra、人工打斷延遲與獨立審查仍未滿足。",
            "- 獨立審查者尚未簽核繞過防護。",
            "- 活的 Claude-only 回滾尚未測試。行程內名稱排練不是正式切換。",
            "",
            "## 診斷",
            "",
        ]
    )
    for note in rehearsal.diagnostics:
        lines.append(f"- {note}")
    lines.append("")
    text = "\n".join(lines)
    if SANDBOX_SECRET in text:
        raise RuntimeError("refusing to render a report that contains the sandbox secret")
    return text


def _cell(value: float | None) -> str:
    if value is None:
        return "unobserved"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _met(metric: MetricValue) -> str:
    return _optional_bool(metric.met)


def _optional_bool(value: bool | None) -> str:
    if value is None:
        return "unobserved"
    return "true" if value else "false"
