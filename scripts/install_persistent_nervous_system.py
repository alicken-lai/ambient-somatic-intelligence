#!/usr/bin/env python3
"""Install local launchd assets for Night 35."""

from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path

from action_log import log_action, stable_json
from guardian_check import classify_action


ROOT = Path(__file__).resolve().parents[1]
LAUNCHD_DIR = ROOT / "launchd"
TICK_PLIST = LAUNCHD_DIR / "ai.ambient-os.dmn-tick.plist"
USER_LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"
INSTALLED_TICK_PLIST = USER_LAUNCH_AGENTS / TICK_PLIST.name
HERMES_SHIM_SRC = ROOT / "tools" / "hermes_mcp_shim" / "mcp_serve.py"
HERMES_SHIM_DST = Path.home() / ".hermes" / "mcp_shim" / "mcp_serve.py"
ROUTE = "persistent-nervous-system-build"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def install_files() -> dict[str, str]:
    result = classify_action("install local launchd plist and reload Hermes MCP shim", ROUTE)
    if result.get("risk") != "ALLOW":
        raise RuntimeError(f"Guardian blocked install: {stable_json(result)}")
    USER_LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    HERMES_SHIM_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TICK_PLIST, INSTALLED_TICK_PLIST)
    shutil.copy2(HERMES_SHIM_SRC, HERMES_SHIM_DST)
    return {
        "tick_plist": str(INSTALLED_TICK_PLIST),
        "hermes_mcp_shim": str(HERMES_SHIM_DST),
    }


def launchd_load() -> dict[str, object]:
    uid = run(["id", "-u"]).stdout.strip()
    target = f"gui/{uid}"
    label = "ai.ambient-os.dmn-tick"
    run(["launchctl", "bootout", target, str(INSTALLED_TICK_PLIST)])
    bootstrap = run(["launchctl", "bootstrap", target, str(INSTALLED_TICK_PLIST)])
    kickstart = run(["launchctl", "kickstart", "-k", f"{target}/{label}"])
    return {
        "bootstrap_returncode": bootstrap.returncode,
        "bootstrap_stderr": bootstrap.stderr.strip(),
        "kickstart_returncode": kickstart.returncode,
        "kickstart_stderr": kickstart.stderr.strip(),
    }


def validate_plist() -> None:
    with TICK_PLIST.open("rb") as handle:
        plistlib.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Night 35 persistent nervous system.")
    parser.add_argument("--load", action="store_true")
    args = parser.parse_args()
    validate_plist()
    installed = install_files()
    launchd = launchd_load() if args.load else {"loaded": False}
    detail = {"installed": installed, "launchd": launchd}
    ok = not args.load or (
        launchd.get("bootstrap_returncode") == 0
        and launchd.get("kickstart_returncode") == 0
    )
    log_action("night35:persistent-install", "completed" if ok else "failed", "ALLOW", detail)
    print(stable_json(detail))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
