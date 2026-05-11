#!/usr/bin/env python3
"""Observe-only visual capture sensor."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_log import log_action, stable_json
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
CUA_ROOT = ROOT / "tools" / "cua"
SCREENSHOT_DIR = CUA_ROOT / "screenshots"
ANALYSIS_DIR = CUA_ROOT / "analysis"
LOG_FILE = CUA_ROOT / "logs" / "vision_capture.jsonl"
POLICY_FILE = CUA_ROOT / "policies" / "observe_only.yaml"

DEFAULT_TARGETS = ("desktop", "terminal", "browser", "grafana")
BLOCKED_ACTIONS = {"click", "type", "scroll", "submit", "drag", "browser navigation"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def load_policy() -> dict[str, list[str]]:
    if not POLICY_FILE.exists():
        raise FileNotFoundError(f"missing policy: {POLICY_FILE.relative_to(ROOT)}")

    policy: dict[str, list[str]] = {"allow": [], "block": []}
    active: str | None = None
    for line in POLICY_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped in {"allow:", "block:"}:
            active = stripped.rstrip(":")
            continue
        if active and stripped.startswith("- "):
            policy[active].append(stripped[2:].strip())
    return policy


def enforce_observe_only() -> None:
    policy = load_policy()
    missing_blocks = sorted(BLOCKED_ACTIONS - set(policy["block"]))
    if missing_blocks:
        raise ValueError(f"observe-only policy missing blocked actions: {', '.join(missing_blocks)}")
    if "screenshot" not in policy["allow"]:
        raise ValueError("observe-only policy must allow screenshot")


def image_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> dict[str, int]:
    completed = run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)])
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    dimensions: dict[str, int] = {}
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("pixelWidth:"):
            dimensions["width"] = int(stripped.split(":", 1)[1].strip())
        if stripped.startswith("pixelHeight:"):
            dimensions["height"] = int(stripped.split(":", 1)[1].strip())
    return dimensions


def bmp_pixels(path: Path) -> tuple[int, int, bytes]:
    with tempfile.TemporaryDirectory() as temp_dir:
        bmp_path = Path(temp_dir) / "capture.bmp"
        completed = run(["sips", "-s", "format", "bmp", str(path), "--out", str(bmp_path)])
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip())
        data = bmp_path.read_bytes()

    if data[:2] != b"BM":
        raise ValueError("expected BMP")
    pixel_offset = int.from_bytes(data[10:14], "little")
    width = int.from_bytes(data[18:22], "little", signed=True)
    height = int.from_bytes(data[22:26], "little", signed=True)
    bits_per_pixel = int.from_bytes(data[28:30], "little")
    if bits_per_pixel not in {24, 32}:
        raise ValueError(f"unsupported BMP depth: {bits_per_pixel}")

    abs_width = abs(width)
    abs_height = abs(height)
    bytes_per_pixel = bits_per_pixel // 8
    row_size = ((bits_per_pixel * abs_width + 31) // 32) * 4
    rgb = bytearray()
    for row in range(abs_height):
        source_row = row if height < 0 else abs_height - row - 1
        row_start = pixel_offset + source_row * row_size
        for column in range(abs_width):
            offset = row_start + column * bytes_per_pixel
            blue, green, red = data[offset], data[offset + 1], data[offset + 2]
            rgb.extend((red, green, blue))
    return abs_width, abs_height, bytes(rgb)


def analyze_image(path: Path, target: str) -> dict[str, Any]:
    width, height, pixels = bmp_pixels(path)
    stride = 3
    total_pixels = max(1, len(pixels) // stride)
    red_warning = 0
    amber_warning = 0
    bright = 0
    dark = 0
    saturated = 0
    for offset in range(0, len(pixels) - 2, stride):
        red, green, blue = pixels[offset], pixels[offset + 1], pixels[offset + 2]
        luminance = (red * 0.2126) + (green * 0.7152) + (blue * 0.0722)
        if red > 190 and green < 95 and blue < 95:
            red_warning += 1
        if red > 190 and 95 <= green <= 175 and blue < 80:
            amber_warning += 1
        if luminance > 220:
            bright += 1
        if luminance < 35:
            dark += 1
        if max(red, green, blue) - min(red, green, blue) > 120:
            saturated += 1

    red_ratio = round(red_warning / total_pixels, 6)
    amber_ratio = round(amber_warning / total_pixels, 6)
    anomaly_notes: list[str] = []
    if red_ratio > 0.01:
        anomaly_notes.append("red warning color density above threshold")
    if amber_ratio > 0.02:
        anomaly_notes.append("amber warning color density above threshold")
    if not anomaly_notes:
        anomaly_notes.append("no visual warning color threshold exceeded")

    return {
        "target": target,
        "dimensions": {"width": width, "height": height},
        "visible_windows": "full desktop capture; window identity not queried",
        "cpu_dashboard": "not visually confirmed" if target != "grafana" else "grafana target captured; dashboard content not OCR-confirmed",
        "warning_indicators": {
            "red_pixel_ratio": red_ratio,
            "amber_pixel_ratio": amber_ratio,
            "saturated_pixel_ratio": round(saturated / total_pixels, 6),
            "bright_pixel_ratio": round(bright / total_pixels, 6),
            "dark_pixel_ratio": round(dark / total_pixels, 6),
        },
        "anomaly_notes": anomaly_notes,
    }


def ocr_image(path: Path) -> dict[str, str]:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return {"status": "unavailable", "text": "", "engine": "none"}
    completed = run([tesseract, str(path), "stdout"])
    if completed.returncode != 0:
        return {"status": "failed", "text": "", "engine": "tesseract"}
    return {"status": "completed", "text": completed.stdout.strip(), "engine": "tesseract"}


def capture(target: str) -> dict[str, Any]:
    enforce_observe_only()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = utc_now()
    stamp = timestamp.replace(":", "").replace("+", "Z")
    screenshot_path = SCREENSHOT_DIR / f"{target}-{stamp}.png"
    completed = run(["screencapture", "-x", str(screenshot_path)])
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "screencapture failed")

    metadata = {
        "timestamp": timestamp,
        "target": target,
        "path": str(screenshot_path.relative_to(ROOT)),
        "sha256": image_sha256(screenshot_path),
        "size_bytes": screenshot_path.stat().st_size,
        "dimensions": image_dimensions(screenshot_path),
        "policy": str(POLICY_FILE.relative_to(ROOT)),
    }
    ocr = ocr_image(screenshot_path)
    analysis = analyze_image(screenshot_path, target)
    record = {
        "metadata": metadata,
        "ocr": {
            "status": ocr["status"],
            "engine": ocr["engine"],
            "text": ocr["text"],
        },
        "analysis": analysis,
    }
    analysis_path = ANALYSIS_DIR / f"{target}-{stamp}.json"
    analysis_path.write_text(stable_json(record) + "\n", encoding="utf-8")

    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(stable_json({"timestamp": utc_now(), "event": "capture", "analysis": str(analysis_path.relative_to(ROOT))}) + "\n")

    dmn_payload = {
        "image_metadata": metadata,
        "ocr_text": ocr["text"],
        "ocr_status": ocr["status"],
        "anomaly_notes": analysis["anomaly_notes"],
        "visible_windows": analysis["visible_windows"],
        "cpu_dashboard": analysis["cpu_dashboard"],
        "warning_indicators": analysis["warning_indicators"],
    }
    append_memory(stable_json(dmn_payload), ["vision", "cua", "observe-only", "night3"], "vision_capture")
    log_action("vision:capture", "completed", "ALLOW", {"target": target, "analysis": str(analysis_path.relative_to(ROOT))})
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture observe-only visual snapshots.")
    parser.add_argument("--target", action="append", choices=DEFAULT_TARGETS)
    args = parser.parse_args()
    targets = args.target or list(DEFAULT_TARGETS)

    results = []
    try:
        for target in targets:
            results.append(capture(target))
    except Exception as exc:
        log_action("vision:capture", "failed", "ALLOW", {"error": str(exc)})
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1

    print(stable_json({"captures": results}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
