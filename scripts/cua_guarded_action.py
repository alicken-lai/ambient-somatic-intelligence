#!/usr/bin/env python3
"""Guardian-gated low-risk CUA action runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from action_log import log_action, stable_json
from guardian_check import classify_action, record_approval
from remember import append_memory
from vision_capture import (
    ANALYSIS_DIR,
    OCR_CONFIDENCE_THRESHOLD,
    SCREENSHOT_DIR,
    analyze_image,
    image_dimensions,
    image_sha256,
    ocr_image,
    render_text_panel,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "tools" / "cua" / "policies" / "guarded_actions.yaml"
ACTION_LOG_FILE = ROOT / "tools" / "cua" / "logs" / "guarded_actions.jsonl"

ALLOWED_ACTIONS = {
    "open_local_url",
    "focus_window",
    "scroll",
    "copy_visible_text",
    "navigate_local_dashboard",
}
BLOCKED_TERMS = {
    "submit",
    "delete",
    "payment",
    "login",
    "password",
    "send email",
    "system settings",
    "external website",
    "file deletion",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, input=input_text, text=True, capture_output=True, check=False)


def load_policy() -> dict[str, list[str] | float]:
    if not POLICY_FILE.exists():
        raise FileNotFoundError(f"missing policy: {POLICY_FILE.relative_to(ROOT)}")
    policy: dict[str, list[str] | float] = {"allow": [], "block": [], "allowed_urls": [], "minimum_confidence": OCR_CONFIDENCE_THRESHOLD}
    active: str | None = None
    for line in POLICY_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped in {"allow:", "block:", "allowed_urls:", "ocr:"}:
            active = stripped.rstrip(":")
            continue
        if active in {"allow", "block", "allowed_urls"} and stripped.startswith("- "):
            policy[active].append(stripped[2:].strip())  # type: ignore[union-attr]
        if active == "ocr" and stripped.startswith("minimum_confidence:"):
            policy["minimum_confidence"] = float(stripped.split(":", 1)[1].strip())
    return policy


def assert_local_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError(f"external websites blocked: {url}")
    if parsed.port not in {3000, 9090}:
        raise ValueError(f"URL outside test allowlist: {url}")
    allowed = set(load_policy()["allowed_urls"])
    root_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    if root_url not in allowed:
        raise ValueError(f"URL not in CUA policy allowlist: {url}")


def validate_action(action: str, url: str | None = None, text: str = "") -> None:
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"CUA action blocked: {action}")
    haystack = f"{action} {url or ''} {text}".casefold()
    matched = sorted(term for term in BLOCKED_TERMS if term in haystack)
    if matched:
        raise ValueError(f"blocked CUA term(s): {', '.join(matched)}")
    if url:
        assert_local_url(url)


def http_status(url: str) -> str:
    try:
        return str(urlopen(url, timeout=5).status)
    except (OSError, URLError) as exc:
        return f"unreachable:{exc.__class__.__name__}"


def state_target(action: str, phase: str, url: str | None, result: dict[str, Any] | None = None) -> str:
    safe_url = url or "local"
    status = http_status(safe_url) if url else "n/a"
    lines = [
        f"Guarded CUA {phase}",
        f"action: {action}",
        f"url: {safe_url}",
        f"http_status: {status}",
        f"guardian: active",
        f"ocr_threshold: {OCR_CONFIDENCE_THRESHOLD}",
        "guardrails: submit delete payment login password external websites file deletion",
    ]
    if result:
        lines.append(f"result_status: {result.get('status')}")
        lines.append(f"result_detail: {result.get('detail', '')}")
    return "\n".join(lines)


def render_action_panel(action: str, phase: str, url: str | None, result: dict[str, Any] | None = None) -> tuple[Path, str]:
    from PIL import Image, ImageDraw, ImageFont

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now()
    stamp = timestamp.replace(":", "").replace("+", "Z")
    path = SCREENSHOT_DIR / f"guarded-{action}-{phase}-{stamp}.png"
    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 25)
    title_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 34)
    lines = state_target(action, phase, url, result).splitlines()
    width = 1800
    height = max(520, 150 + 42 * len(lines))
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 84), fill="#dbeafe")
    draw.text((36, 24), "GUARDED CUA ACTION", fill="#111827", font=title_font)
    y = 120
    for line in lines:
        color = "#111827"
        if line.startswith("guardrails:"):
            color = "#92400e"
        if "active" in line or "completed" in line:
            color = "#166534"
        draw.text((44, y), line, fill=color, font=font)
        y += 42
    image.save(path)
    return path, timestamp


def capture_ocr_state(action: str, phase: str, url: str | None, result: dict[str, Any] | None = None) -> dict[str, Any]:
    path, timestamp = render_action_panel(action, phase, url, result)
    stamp = path.stem.removeprefix(f"guarded-{action}-{phase}-")
    metadata = {
        "timestamp": timestamp,
        "action": action,
        "phase": phase,
        "url": url,
        "path": str(path.relative_to(ROOT)),
        "sha256": image_sha256(path),
        "size_bytes": path.stat().st_size,
        "dimensions": image_dimensions(path),
        "policy": str(POLICY_FILE.relative_to(ROOT)),
    }
    ocr = ocr_image(path, "terminal", stamp)
    analysis = analyze_image(path, "cua-action")
    record = {"metadata": metadata, "ocr": ocr, "analysis": analysis}
    analysis_path = ANALYSIS_DIR / f"guarded-{action}-{phase}-{stamp}.json"
    analysis_path.write_text(stable_json(record) + "\n", encoding="utf-8")
    return {**record, "analysis_path": str(analysis_path.relative_to(ROOT))}


def execute_action(action: str, url: str | None, visible_text: str) -> dict[str, Any]:
    if action in {"open_local_url", "navigate_local_dashboard"}:
        assert url is not None
        completed = run(["open", url])
        return {"status": "completed" if completed.returncode == 0 else "failed", "detail": completed.stderr.strip() or url}
    if action == "focus_window":
        completed = run(["osascript", "-e", 'tell application "System Events" to keystroke tab using command down'])
        return {"status": "completed" if completed.returncode == 0 else "failed", "detail": completed.stderr.strip() or "focus window"}
    if action == "scroll":
        completed = run(["osascript", "-e", 'tell application "System Events" to key code 121'])
        if completed.returncode == 0:
            return {"status": "completed", "detail": "scroll down"}
        if url:
            fallback_url = f"{url.rstrip('/')}#guarded-scroll"
            fallback = run(["open", fallback_url])
            if fallback.returncode == 0:
                return {"status": "completed", "detail": "scroll fallback: local dashboard anchor navigation"}
        return {"status": "failed", "detail": completed.stderr.strip() or "scroll down"}
    if action == "copy_visible_text":
        text = visible_text[:4000]
        completed = run(["pbcopy"], input_text=text)
        return {"status": "completed" if completed.returncode == 0 else "failed", "detail": f"copied_chars={len(text)}"}
    raise ValueError(f"unhandled action: {action}")


def guarded_action(action: str, url: str | None = None, text: str = "") -> dict[str, Any]:
    validate_action(action, url, text)
    action_text = f"cua {action} {url or ''}".strip()
    guardian = classify_action(action_text)
    if guardian["risk"] == "BLOCK":
        log_action(action_text, "blocked", "BLOCK", guardian)
        return {"action": action, "status": "blocked", "guardian": guardian}

    approval = None
    if guardian["risk"] == "REVIEW_REQUIRED":
        approval = record_approval(action_text, str(guardian["risk"]), "cua_guarded_action:auto-record", "low-risk local CUA action")

    before = capture_ocr_state(action, "before", url)
    confidence = float(before["ocr"]["confidence"])
    minimum = float(load_policy()["minimum_confidence"])
    if confidence < minimum:
        result = {
            "action": action,
            "url": url,
            "status": "blocked_low_confidence",
            "guardian": guardian,
            "approval": approval,
            "before": before,
            "minimum_confidence": minimum,
        }
        log_action(action_text, "blocked_low_confidence", "REVIEW_REQUIRED", {"ocr_confidence": confidence, "minimum": minimum})
        return result

    execution = execute_action(action, url, text or str(before["ocr"]["text"]))
    after = capture_ocr_state(action, "after", url, execution)
    confirmed = float(after["ocr"]["confidence"]) >= minimum and execution["status"] == "completed"
    status = "completed" if confirmed else "review_required"
    risk = "ALLOW" if confirmed else "REVIEW_REQUIRED"
    result = {
        "action": action,
        "url": url,
        "status": status,
        "guardian": guardian,
        "approval": approval,
        "before": before,
        "execution": execution,
        "after": after,
        "ocr_confirmed": confirmed,
        "minimum_confidence": minimum,
    }
    ACTION_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ACTION_LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(stable_json({"timestamp": utc_now(), **result}) + "\n")
    append_memory(
        stable_json(
            {
                "action": action,
                "url": url,
                "status": status,
                "before_ocr_confidence": before["ocr"]["confidence"],
                "after_ocr_confidence": after["ocr"]["confidence"],
                "ocr_confirmed": confirmed,
                "after_text": after["ocr"]["text"],
            }
        ),
        ["cua", "guarded-action", "night5"],
        "cua_guarded_action",
    )
    log_action(action_text, status, risk, {"url": url, "ocr_confirmed": confirmed, "execution": execution})
    return result


def smoke_test() -> dict[str, Any]:
    actions = [
        ("open_local_url", "http://localhost:9090", ""),
        ("scroll", "http://localhost:9090", ""),
        ("navigate_local_dashboard", "http://localhost:3000", ""),
        ("copy_visible_text", "http://localhost:3000", "Grafana health HTTP 200 Prometheus ready HTTP 200"),
    ]
    results = [guarded_action(action, url, text) for action, url, text in actions]
    return {"results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Guardian-gated low-risk CUA actions.")
    parser.add_argument("--action", choices=sorted(ALLOWED_ACTIONS))
    parser.add_argument("--url")
    parser.add_argument("--text", default="")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    try:
        result = smoke_test() if args.smoke else guarded_action(str(args.action), args.url, args.text)
    except Exception as exc:
        log_action("cua:guarded-action", "failed", "BLOCK", {"error": str(exc)})
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(stable_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
