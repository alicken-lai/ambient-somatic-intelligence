#!/usr/bin/env python3
"""Build the local Somatic Dashboard from existing observability artifacts."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, record_checksum, stable_json


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "dashboard"
DASHBOARD_HTML = DASHBOARD_DIR / "index.html"
STATE_JSON = ROOT / "state" / "system_state.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "n/a"


def build_model() -> dict[str, Any]:
    model = load_json(STATE_JSON)
    if not model:
        raise RuntimeError("state/system_state.json is missing; run system-state-build first")
    model["sources"] = {
        key: value.get("path", "")
        for key, value in model.get("authoritative_sources", {}).items()
    }
    model["dashboard_generated_at"] = utc_now()
    return model


def bar(score: Any) -> str:
    try:
        value = max(0.0, min(100.0, float(score)))
    except (TypeError, ValueError):
        value = 0.0
    return f'<div class="bar"><span style="width: {value:.2f}%"></span></div>'


def render_html(model: dict[str, Any]) -> str:
    subsystem_rows = []
    for name, data in model["subsystems"].items():
        subsystem_rows.append(
            "<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td>{pct(data.get('score'))}</td>"
            f"<td>{bar(data.get('score'))}</td>"
            f"<td>{pct(data.get('incident_penalty'))}</td>"
            "</tr>"
        )

    containers = model["docker_context"]["containers"]
    container_rows = []
    for container in containers:
        container_rows.append(
            "<tr>"
            f"<td>{html.escape(str(container.get('name', 'unknown')))}</td>"
            f"<td>{html.escape(str(container.get('memory_usage', 'n/a')))}</td>"
            f"<td>{html.escape(str(container.get('memory_percent', 'n/a')))}</td>"
            f"<td>{html.escape(str(container.get('cpu_percent', 'n/a')))}</td>"
            "</tr>"
        )
    if not container_rows:
        container_rows.append('<tr><td colspan="4">No container stats recorded.</td></tr>')

    repeated = model["repeated_anomalies"]
    repeated_text = ", ".join(f"{key}: {value}" for key, value in repeated.items()) or "none"
    vm = model["docker_context"]["vm"]
    recommendations = "".join(f"<li>{html.escape(item)}</li>" for item in model["recommendations"])
    sources = "".join(f"<li>{html.escape(key)}: <code>{html.escape(value)}</code></li>" for key, value in model["sources"].items())

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Somatic Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7f9;
      --panel: #ffffff;
      --ink: #172026;
      --muted: #60717d;
      --line: #d9e1e7;
      --good: #1f8a70;
      --watch: #b7791f;
      --review: #9b4dca;
      --incident: #c2413d;
      --accent: #245c7a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: flex-end;
      border-bottom: 1px solid var(--line);
      padding-bottom: 16px;
      margin-bottom: 20px;
    }}
    h1, h2 {{ margin: 0; }}
    h1 {{ font-size: 30px; letter-spacing: 0; }}
    h2 {{ font-size: 17px; margin-bottom: 12px; }}
    .stamp {{ color: var(--muted); font-size: 13px; text-align: right; }}
    .refresh-control {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .refresh-control input {{
      width: 16px;
      height: 16px;
      accent-color: var(--accent);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 14px;
    }}
    section, .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .metric {{ min-height: 116px; }}
    .span-3 {{ grid-column: span 3; }}
    .span-4 {{ grid-column: span 4; }}
    .span-6 {{ grid-column: span 6; }}
    .span-8 {{ grid-column: span 8; }}
    .span-12 {{ grid-column: span 12; }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }}
    .value {{ font-size: 34px; font-weight: 700; margin-top: 8px; }}
    .small {{ color: var(--muted); font-size: 13px; margin-top: 6px; word-break: break-word; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: #eaf1f4;
      color: var(--accent);
      margin-top: 10px;
    }}
    .watch {{ color: var(--watch); }}
    .review {{ color: var(--review); }}
    .incident {{ color: var(--incident); }}
    .steady {{ color: var(--good); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 9px 6px; vertical-align: middle; }}
    th {{ color: var(--muted); font-weight: 600; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .bar {{ height: 8px; background: #edf2f5; border-radius: 999px; overflow: hidden; }}
    .bar span {{ display: block; height: 100%; background: var(--accent); border-radius: 999px; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li + li {{ margin-top: 6px; }}
    @media (max-width: 820px) {{
      header {{ display: block; }}
      .stamp {{ text-align: left; margin-top: 8px; }}
      .span-3, .span-4, .span-6, .span-8 {{ grid-column: span 12; }}
      .value {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Somatic Dashboard</h1>
        <div class="small">Local body state, reflex confidence, incident memory, and memory pressure.</div>
      </div>
      <div class="stamp">
        Generated {html.escape(model['generated_at'])}<br>No corrective actions. Recommendations only.
        <label class="refresh-control">
          <input id="auto-refresh" type="checkbox" aria-label="Auto refresh dashboard">
          Auto-refresh 60s
        </label>
      </div>
    </header>

    <div class="grid">
      <div class="metric span-3">
        <div class="label">Overall Health</div>
        <div class="value {html.escape(model['health_risk'])}">{pct(model['health_score'])}</div>
        <div class="pill">{html.escape(model['health_risk'])}</div>
      </div>
      <div class="metric span-3">
        <div class="label">Trend</div>
        <div class="value">{html.escape(str(model['trend']))}</div>
        <div class="small">current temporal direction</div>
      </div>
      <div class="metric span-3">
        <div class="label">Reflex Confidence</div>
        <div class="value {html.escape(model['display_risk'])}">{model['latest_reflex_confidence']:.2f}</div>
        <div class="pill">{html.escape(model['current_risk_class'])}</div>
      </div>
      <div class="metric span-3">
        <div class="label">Incidents</div>
        <div class="value">{model['incident_count']}</div>
        <div class="small">Repeated anomalies: {model['repeated_anomaly_count']} ({html.escape(repeated_text)})</div>
      </div>

      <section class="span-8">
        <h2>Subsystem Scores</h2>
        <table>
          <thead><tr><th>Subsystem</th><th>Score</th><th>State</th><th>Incident Penalty</th></tr></thead>
          <tbody>{''.join(subsystem_rows)}</tbody>
        </table>
      </section>

      <section class="span-4">
        <h2>Memory Status</h2>
        <table>
          <tbody>
            <tr><th>Used</th><td>{html.escape(str(model['memory_status']['used_percent']))}%</td></tr>
            <tr><th>Free Bytes</th><td>{html.escape(str(model['memory_status']['free_bytes']))}</td></tr>
            <tr><th>Risk</th><td>{html.escape(str(model['memory_status']['true_risk']))}</td></tr>
            <tr><th>Artifact</th><td>{html.escape(str(model['memory_status']['scoring_artifact']))}</td></tr>
            <tr><th>Swap</th><td><code>{html.escape(str(model['memory_status']['swap']))}</code></td></tr>
          </tbody>
        </table>
      </section>

      <section class="span-6">
        <h2>Docker Context</h2>
        <table>
          <tbody>
            <tr><th>VM Detected</th><td>{html.escape(str(vm.get('detected')))}</td></tr>
            <tr><th>VM Memory MiB</th><td>{html.escape(str(vm.get('memory_mib')))}</td></tr>
            <tr><th>VM CPUs</th><td>{html.escape(str(vm.get('cpus')))}</td></tr>
            <tr><th>VM RSS MB</th><td>{html.escape(str(vm.get('rss_mb')))}</td></tr>
          </tbody>
        </table>
      </section>

      <section class="span-6">
        <h2>Container Memory</h2>
        <table>
          <thead><tr><th>Name</th><th>Memory</th><th>Memory %</th><th>CPU %</th></tr></thead>
          <tbody>{''.join(container_rows)}</tbody>
        </table>
      </section>

      <section class="span-6">
        <h2>Memory Links</h2>
        <table>
          <tbody>
            <tr><th>Latest Telemetry</th><td><code>{html.escape(str(model['latest_telemetry_snapshot']))}</code></td></tr>
            <tr><th>DMN Append Count</th><td>{model['dmn_append_count']}</td></tr>
            <tr><th>Baseline Deviation</th><td>{html.escape(str(model['baseline_deviation']['overall_severity']))}</td></tr>
          </tbody>
        </table>
      </section>

      <section class="span-6">
        <h2>Recommendations</h2>
        <ul>{recommendations}</ul>
      </section>

      <section class="span-12">
        <h2>Sources</h2>
        <ul>{sources}</ul>
      </section>
    </div>
  </main>
  <script>
    (function () {{
      var checkbox = document.getElementById("auto-refresh");
      var key = "somaticDashboardAutoRefresh";
      var timer = null;
      function applyRefresh(enabled) {{
        window.localStorage.setItem(key, enabled ? "1" : "0");
        if (timer) {{
          window.clearInterval(timer);
          timer = null;
        }}
        if (enabled) {{
          timer = window.setInterval(function () {{
            window.location.reload();
          }}, 60000);
        }}
      }}
      checkbox.checked = window.localStorage.getItem(key) === "1";
      applyRefresh(checkbox.checked);
      checkbox.addEventListener("change", function () {{
        applyRefresh(checkbox.checked);
      }});
    }})();
  </script>
</body>
</html>
"""


def build_dashboard() -> dict[str, Any]:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    model = build_model()
    DASHBOARD_HTML.write_text(render_html(model), encoding="utf-8")
    record_checksum(DASHBOARD_HTML, "somatic_dashboard_build", {"source": str(STATE_JSON.relative_to(ROOT))})
    memory = {
        "dashboard": str(DASHBOARD_HTML.relative_to(ROOT)),
        "health_score": model["health_score"],
        "current_risk_class": model["current_risk_class"],
        "incident_count": model["incident_count"],
        "dmn_append_count": model["dmn_append_count"],
        "baseline_deviation": model["baseline_deviation"]["overall_severity"],
        "recommendations_only": True,
    }
    log_action("dashboard:somatic-build", "completed", "ALLOW", memory)
    return memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the local Somatic Dashboard.")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if not args.build:
        parser.error("--build is required")
    print(stable_json(build_dashboard()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
