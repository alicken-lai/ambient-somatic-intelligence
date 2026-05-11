#!/usr/bin/env python3
"""Minimal Guardian command risk classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "guardian" / "policy.yaml"


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


def classify_action(action: str) -> dict[str, object]:
    normalized = action.casefold()
    blocked = [keyword for keyword in _load_keyword_list("blocked_keywords") if keyword.casefold() in normalized]
    if blocked:
        return {"risk": "BLOCK", "matched": blocked, "action": action}

    review = [keyword for keyword in _load_keyword_list("review_keywords") if keyword.casefold() in normalized]
    if review:
        return {"risk": "REVIEW_REQUIRED", "matched": review, "action": action}

    return {"risk": "ALLOW", "matched": [], "action": action}


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify an action against Guardian policy.")
    parser.add_argument("action")
    args = parser.parse_args()
    result = classify_action(args.action)
    print(json.dumps(result, sort_keys=True))
    return 2 if result["risk"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())

