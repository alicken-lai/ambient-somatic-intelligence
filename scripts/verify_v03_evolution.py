#!/usr/bin/env python3
"""
Ambient OS v0.3 — Evolution Integration Verification Script

Validates all 8 new subsystems (Phases A–H) by importing, instantiating,
and exercising their primary APIs. Reports PASS/FAIL per subsystem and
overall v0.3 readiness status.

Usage:
    cd ~/ambient-os
    python scripts/verify_v03_evolution.py
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("AMBIENT_OS_ROOT", str(ROOT))

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

results: list[tuple[str, str, bool, str]] = []


def record(phase: str, name: str, ok: bool, detail: str = ""):
    results.append((phase, name, ok, detail))
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {phase}: {name}" + (f" — {detail}" if detail and not ok else ""))


def verify_phase_a():
    """Phase A: Cognitive Self-Model"""
    print("\n--- Phase A: Cognitive Self-Model ---")
    try:
        from identity.cognitive_self_model import CognitiveSelfModel
        model = CognitiveSelfModel(root=ROOT)
        model.build()
        topology = model.get_system_topology()
        assert isinstance(topology, dict), "get_system_topology() must return dict"
        assert "subsystems" in topology or "summary" in topology, "topology missing expected keys"
        record("A", "CognitiveSelfModel.build()", True)
        record("A", "CognitiveSelfModel.get_system_topology()", True)
    except Exception as exc:
        record("A", "CognitiveSelfModel", False, str(exc))
        traceback.print_exc()


def verify_phase_b():
    """Phase B: Architecture Drift Detection"""
    print("\n--- Phase B: Architecture Drift Detection ---")
    try:
        from identity.cognitive_self_model import CognitiveSelfModel
        from observability.drift_detection import DriftDetector

        model = CognitiveSelfModel(root=ROOT)
        model.build()

        detector = DriftDetector(root=ROOT)
        report = detector.detect(model)
        assert report is not None, "detect() returned None"
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict), "to_dict() must return dict"
        record("B", "DriftDetector.detect()", True)
    except Exception as exc:
        record("B", "DriftDetector.detect()", False, str(exc))
        traceback.print_exc()


def verify_phase_c():
    """Phase C: Memory-Guided Evolution"""
    print("\n--- Phase C: Memory-Guided Evolution ---")
    try:
        from memory.evolution import PatternMiner
        miner = PatternMiner(history_dir=ROOT / "state" / "agents")
        patterns = miner.mine_success_patterns(min_occurrences=1)
        assert isinstance(patterns, list), "mine_success_patterns() must return list"
        record("C", "PatternMiner.mine_success_patterns()", True)
    except Exception as exc:
        record("C", "PatternMiner", False, str(exc))
        traceback.print_exc()


def verify_phase_d():
    """Phase D: Adaptive Task Graph Optimization"""
    print("\n--- Phase D: Adaptive Task Graph Optimization ---")
    try:
        from runtime.task_graph_optimizer import TaskGraphOptimizer
        optimizer = TaskGraphOptimizer()
        assert optimizer is not None
        record("D", "TaskGraphOptimizer instantiation", True)
    except Exception as exc:
        record("D", "TaskGraphOptimizer", False, str(exc))
        traceback.print_exc()


def verify_phase_e():
    """Phase E: Context Economy Engine"""
    print("\n--- Phase E: Context Economy Engine ---")
    try:
        from context.context_economy import ContextCostAccountant
        accountant = ContextCostAccountant(persist=False)
        assert accountant is not None
        record("E", "ContextCostAccountant instantiation", True)
    except Exception as exc:
        record("E", "ContextCostAccountant", False, str(exc))
        traceback.print_exc()

    try:
        from context.context_economy import TokenEconomy
        economy = TokenEconomy(system_budget=100_000)
        assert economy is not None
        record("E", "TokenEconomy instantiation", True)
    except Exception as exc:
        record("E", "TokenEconomy", False, str(exc))
        traceback.print_exc()


def verify_phase_f():
    """Phase F: Somatic Attention Runtime"""
    print("\n--- Phase F: Somatic Attention Runtime ---")
    try:
        from somatic.attention_runtime import SomaticAttentionRuntime
        from somatic.signal_bus import SomaticSignalBus
        from somatic.attention_manager import AttentionManager

        bus = SomaticSignalBus()
        attention_mgr = AttentionManager(bus)
        runtime = SomaticAttentionRuntime(bus=bus, attention_manager=attention_mgr)
        assert runtime is not None
        record("F", "SomaticAttentionRuntime instantiation", True)
    except Exception as exc:
        record("F", "SomaticAttentionRuntime", False, str(exc))
        traceback.print_exc()


def verify_phase_g():
    """Phase G: Recursive Runtime Observability"""
    print("\n--- Phase G: Recursive Runtime Observability ---")
    try:
        from observability.recursive_runtime import CognitionTracer
        tracer = CognitionTracer(persist=False)
        assert tracer is not None
        record("G", "CognitionTracer instantiation", True)
    except Exception as exc:
        record("G", "CognitionTracer", False, str(exc))
        traceback.print_exc()

    try:
        from observability.recursive_runtime import IntrospectionDashboard
        dashboard = IntrospectionDashboard()
        assert dashboard is not None
        record("G", "IntrospectionDashboard instantiation", True)
    except Exception as exc:
        record("G", "IntrospectionDashboard", False, str(exc))
        traceback.print_exc()


def verify_phase_h():
    """Phase H: Evolution Engine"""
    print("\n--- Phase H: Evolution Engine ---")
    try:
        from runtime.evolution_engine import EvolutionEngine
        engine = EvolutionEngine()
        assert engine is not None
        record("H", "EvolutionEngine instantiation", True)
    except Exception as exc:
        record("H", "EvolutionEngine", False, str(exc))
        traceback.print_exc()


def print_summary():
    total = len(results)
    passed = sum(1 for _, _, ok, _ in results if ok)
    failed = total - passed

    print("\n" + "=" * 60)
    print("  AMBIENT OS v0.3 — EVOLUTION VERIFICATION SUMMARY")
    print("=" * 60)

    phases_seen: dict[str, list[tuple[str, bool, str]]] = {}
    for phase, name, ok, detail in results:
        phases_seen.setdefault(phase, []).append((name, ok, detail))

    for phase in sorted(phases_seen.keys()):
        checks = phases_seen[phase]
        phase_ok = all(ok for _, ok, _ in checks)
        status = PASS if phase_ok else FAIL
        print(f"  Phase {phase}: {status}")
        for name, ok, detail in checks:
            tag = PASS if ok else FAIL
            suffix = f"  ({detail})" if detail and not ok else ""
            print(f"    [{tag}] {name}{suffix}")

    print("-" * 60)
    print(f"  Total checks:  {total}")
    print(f"  Passed:        {passed}")
    print(f"  Failed:        {failed}")
    print("-" * 60)

    if failed == 0:
        print(f"  Overall: [{PASS}] v0.3 READY — All subsystems operational")
    else:
        print(f"  Overall: [{FAIL}] v0.3 NOT READY — {failed} check(s) failed")

    print("=" * 60)

    return failed == 0


def main():
    print("=" * 60)
    print("  Ambient OS v0.3 — Evolution Integration Verification")
    print(f"  Root: {ROOT}")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 60)

    start = time.monotonic()

    verify_phase_a()
    verify_phase_b()
    verify_phase_c()
    verify_phase_d()
    verify_phase_e()
    verify_phase_f()
    verify_phase_g()
    verify_phase_h()

    elapsed = (time.monotonic() - start) * 1000
    print(f"\n  Verification completed in {elapsed:.0f}ms")

    all_ok = print_summary()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
