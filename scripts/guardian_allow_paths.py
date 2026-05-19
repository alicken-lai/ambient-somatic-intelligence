"""Path allowlist helpers for Hermes Guardian (shared by hook and CLI)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "guardian" / "policy.yaml"
ALLOWED_PATHS_FILE = ROOT / "guardian" / "allowed_paths.yaml"


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


def load_allowed_paths() -> list[str]:
    paths = _load_keyword_list("allowed_paths")
    if ALLOWED_PATHS_FILE.exists():
        for line in ALLOWED_PATHS_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                paths.append(stripped[2:].strip())
    return paths


def normalize_path_for_match(value: str) -> str:
    return value.replace("\\", "/").casefold()


def action_matches_allowed_path(action: str) -> bool:
    allowed = load_allowed_paths()
    if not allowed:
        return False
    normalized_action = normalize_path_for_match(action)
    return any(
        normalize_path_for_match(pattern) in normalized_action for pattern in allowed
    )


def apply_allowlist(
    action: str,
    classify_fn: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    if action_matches_allowed_path(action):
        return {"risk": "ALLOW", "matched": ["allowed_path"], "action": action}
    return classify_fn(action)
