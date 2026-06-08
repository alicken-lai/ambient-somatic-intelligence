#!/usr/bin/env python3
"""Minimal Guardian command risk classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from action_log import append_jsonl, log_action, record_checksum, utc_now


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "guardian" / "policy.yaml"
BOUNDARY_FILE = ROOT / "guardian" / "decision_boundary.yaml"
APPROVALS_FILE = ROOT / "guardian" / "approvals.jsonl"


def _load_keyword_list(section: str) -> list[str]:
    if not POLICY_FILE.exists():
        return []

    keywords: list[str] = []
    active = False
    for line in POLICY_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == f"{section}:":
            active = True
            continue
        if active and stripped.endswith(":") and not stripped.startswith("-"):
            break
        if active and stripped.startswith("- "):
            keywords.append(stripped[2:].strip())
    return keywords


def _action_matches_allowed_path(action: str) -> bool:
    import sys

    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from guardian_allow_paths import action_matches_allowed_path

    return action_matches_allowed_path(action)


def _load_boundary_config() -> dict[str, dict[str, str]]:
    if not BOUNDARY_FILE.exists():
        return {"levels": {}, "routes": {}}

    config: dict[str, dict[str, str]] = {"levels": {}, "routes": {}}
    section: str | None = None
    for raw_line in BOUNDARY_FILE.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "levels:":
            section = "levels"
            continue
        if stripped == "routes:":
            section = "routes"
            continue
        if section == "levels" and raw_line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            config["levels"][key.strip()] = value.strip()
        if section == "routes" and raw_line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            config["routes"][key.strip()] = value.strip()
    return config


def route_boundary_level(route_name: str | None) -> str:
    if not route_name:
        return "OBSERVE_ONLY"
    config = _load_boundary_config()
    return config.get("routes", {}).get(route_name, "OBSERVE_ONLY")


def classify_action(action: str, route_name: str | None = None) -> dict[str, object]:
    if _action_matches_allowed_path(action):
        result = {"risk": "ALLOW", "matched": ["allowed_path"], "action": action}
        if route_name:
            result["boundary_level"] = route_boundary_level(route_name)
        return result

    normalized = action.casefold()
    blocked = [keyword for keyword in _load_keyword_list("blocked_keywords") if keyword.casefold() in normalized]
    if blocked:
        result = {"risk": "BLOCK", "matched": blocked, "action": action}
        if route_name:
            result["boundary_level"] = route_boundary_level(route_name)
        return result

    review = [keyword for keyword in _load_keyword_list("review_keywords") if keyword.casefold() in normalized]
    if review:
        result = {"risk": "REVIEW_REQUIRED", "matched": review, "action": action}
        if route_name:
            result["boundary_level"] = route_boundary_level(route_name)
        return result

    result = {"risk": "ALLOW", "matched": [], "action": action}
    if route_name:
        result["boundary_level"] = route_boundary_level(route_name)
    return result


def record_approval(action: str, risk: str, approver: str, reason: str = "") -> dict[str, Any]:
    record = {
        "timestamp": utc_now(),
        "action": action,
        "risk": risk,
        "approver": approver,
        "reason": reason,
    }
    append_jsonl(APPROVALS_FILE, record)
    record_checksum(APPROVALS_FILE, "guardian_approval_append", {"action": action, "risk": risk})
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify an action against Guardian policy.")
    parser.add_argument("action")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--approver", default="guardian-cli")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    result = classify_action(args.action)
    approval = None
    if args.approve and result["risk"] == "REVIEW_REQUIRED":
        approval = record_approval(args.action, str(result["risk"]), args.approver, args.reason)
        result["approval"] = approval
    log_action(args.action, "classified", str(result["risk"]), result)
    print(json.dumps(result, sort_keys=True))
    return 2 if result["risk"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
