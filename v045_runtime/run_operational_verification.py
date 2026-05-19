#!/usr/bin/env python3
"""Single entry: v0.4.5 operational runtime verification (Phases 0–10)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from kernel.entropy.entropy_controller import EntropyController
from kernel.entropy.stale_state_detector import StaleStateDetector
from kernel.truth import Mutability, TruthGraph, TruthNode
from observability.v04.operational_stability_score import (
    compute_operational_stability,
)
from v045_runtime.simulations import load_window_params, run_all_phases


RUNTIME_DIR = Path(__file__).resolve().parent
REPORTS_DIR = RUNTIME_DIR / "reports"
MATRIX_PATH = RUNTIME_DIR / "runtime_test_matrix.json"


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _boot_graph_and_controller() -> tuple[TruthGraph, EntropyController]:
    graph = TruthGraph()
    node = TruthNode.create(
        node_id="runtime:baseline",
        source="v045_runtime",
        owner="verification",
        version="1.0",
        mutability=Mutability.IMMUTABLE,
        payload={"phase": "baseline"},
    )
    graph.register_node(node)
    controller = EntropyController(stale_detector=StaleStateDetector(REPO_ROOT))
    return graph, controller


def _report_entropy(r: dict) -> str:
    return f"""# Entropy Runtime Report (Phase 1)

**Generated:** {_ts()}  
**Mode:** accelerated simulation

## Results

| Metric | Value | Target |
|--------|-------|--------|
| Samples | {r['samples']} | — |
| Max entropy | {r['max_entropy']:.4f} | < 0.30 |
| Mean entropy | {r['mean_entropy']:.4f} | — |
| Drift slope | {r['drift_slope']:.6f} | ≤ 0.002 |
| Exponential drift | {r['exponential_drift']} | false |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_patch(r: dict) -> str:
    return f"""# Patch Registry Runtime Report (Phase 2)

**Generated:** {_ts()}

| Metric | Value | Target |
|--------|-------|--------|
| Wire/unwire cycles | {r['cycles']} | — |
| Leakage | {r['leakage']} | 0 |
| Duplicates | {r['duplicates']} | 0 |
| Unwire repro rate | {r['unwire_repro_rate']:.4f} | 1.0 |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_isolation(r: dict) -> str:
    return f"""# Isolation Runtime Report (Phase 3)

**Generated:** {_ts()}

| Metric | Value | Target |
|--------|-------|--------|
| Parallel contexts | {r['parallel_contexts']} | — |
| Sandbox leaks | {r['sandbox_leaks']} | 0 |
| Isolation score | {r['isolation_score']:.4f} | ≥ 0.85 |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_trace(r: dict) -> str:
    return f"""# Authority Trace Runtime Report (Phase 4)

**Generated:** {_ts()}

| Metric | Value | Target |
|--------|-------|--------|
| Emissions | {r['emissions']} | — |
| Cap | {r['cap']} | — |
| Stored events | {r['stored_events']} | ≤ cap |
| Bounded | {r['bounded']} | true |
| Growth rate | {r['growth_rate']:.4f} | no runaway |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_daemon(r: dict) -> str:
    return f"""# Daemon Runtime Report (Phase 5)

**Generated:** {_ts()}

| Metric | Value | Target |
|--------|-------|--------|
| Simulated ticks | {r['simulated_ticks']} | — |
| DMN tick status ok | {r['dmn_tick_status_ok']} | true |
| Tick gaps | {r['tick_gaps']} | 0 |
| Maturation continuity | {r['maturation_continuity']:.4f} | ≥ 0.95 |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_truthgraph(r: dict) -> str:
    return f"""# TruthGraph Runtime Report (Phase 6)

**Generated:** {_ts()}

| Metric | Value | Target |
|--------|-------|--------|
| Simulated ticks | {r['ticks']} | — |
| Nodes registered | {r['nodes']} | — |
| Final stability | {r['final_stability']:.4f} | ≥ 0.85 |
| Min stability | {r['min_stability']:.4f} | — |
| Conflicts | {r['conflicts']} | 0 |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_replay(r: dict) -> str:
    return f"""# Replay Runtime Report (Phase 7)

**Generated:** {_ts()}

| Metric | Value | Target |
|--------|-------|--------|
| Replay rounds | {r['rounds']} | — |
| Match rate | {r['match_rate']:.4f} | 1.0 |

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def _report_failures(r: dict) -> str:
    lines = "\n".join(
        f"- **{d['type']}**: recovered={d['recovered']}" for d in r["details"]
    )
    return f"""# Failure Mode Simulation (Phase 9)

**Generated:** {_ts()}

Injections: {r['injections']}  
Recovered: {r['recovered']}  
Recovery rate: {r['recovery_rate']:.4f}

## Details

{lines}

## Verdict

**{'PASS' if r['pass'] else 'FAIL'}**
"""


def main() -> int:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    window = matrix.get("gate_window", "72h")
    params = load_window_params(MATRIX_PATH, window)
    graph, controller = _boot_graph_and_controller()
    phases = run_all_phases(params, REPO_ROOT, controller, graph)
    op_report = compute_operational_stability(phases.evidence)

    _write(REPORTS_DIR / "entropy_runtime_report.md", _report_entropy(phases.entropy))
    _write(
        REPORTS_DIR / "entropy_drift_timeseries.json",
        json.dumps(
            {
                "window": window,
                "generated_at": _ts(),
                "tail": phases.entropy.get("series_tail", []),
                "max_entropy": phases.entropy["max_entropy"],
                "drift_slope": phases.entropy["drift_slope"],
            },
            indent=2,
        ),
    )
    _write(REPORTS_DIR / "patch_runtime_report.md", _report_patch(phases.patch))
    _write(REPORTS_DIR / "isolation_runtime_report.md", _report_isolation(phases.isolation))
    _write(
        REPORTS_DIR / "authority_trace_runtime_report.md",
        _report_trace(phases.authority_trace),
    )
    _write(REPORTS_DIR / "daemon_runtime_report.md", _report_daemon(phases.daemon))
    _write(REPORTS_DIR / "truthgraph_runtime_report.md", _report_truthgraph(phases.truthgraph))
    _write(REPORTS_DIR / "replay_runtime_report.md", _report_replay(phases.replay))
    _write(REPORTS_DIR / "failure_mode_simulation.md", _report_failures(phases.failure_modes))

    summary = {
        "generated_at": _ts(),
        "window": window,
        "simulation_mode": "accelerated",
        "operational_stability_score": op_report.score,
        "gate_pass": op_report.gate_pass,
        "classification": op_report.classification.value,
        "hard_failures": op_report.hard_failures,
        "dimensions": op_report.dimensions,
        "phases": {
            "entropy": phases.entropy["pass"],
            "patch": phases.patch["pass"],
            "isolation": phases.isolation["pass"],
            "authority_trace": phases.authority_trace["pass"],
            "daemon": phases.daemon["pass"],
            "truthgraph": phases.truthgraph["pass"],
            "replay": phases.replay["pass"],
            "failure_modes": phases.failure_modes["pass"],
        },
    }
    _write(
        REPORTS_DIR / "operational_stability_summary.json",
        json.dumps(summary, indent=2),
    )

    print(json.dumps(summary, indent=2))
    return 0 if op_report.gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
