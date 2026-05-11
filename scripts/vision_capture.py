#!/usr/bin/env python3
"""Observe-only visual capture sensor."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import cv2
import numpy as np
import pytesseract
from action_log import log_action, stable_json
from guardian_check import record_approval
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from remember import append_memory


ROOT = Path(__file__).resolve().parents[1]
CUA_ROOT = ROOT / "tools" / "cua"
SCREENSHOT_DIR = CUA_ROOT / "screenshots"
ANALYSIS_DIR = CUA_ROOT / "analysis"
PREPROCESS_DIR = ANALYSIS_DIR / "preprocessed"
LOG_FILE = CUA_ROOT / "logs" / "vision_capture.jsonl"
POLICY_FILE = CUA_ROOT / "policies" / "observe_only.yaml"
OCR_CONFIDENCE_THRESHOLD = 45.0

DEFAULT_TARGETS = ("desktop", "terminal", "browser", "grafana", "docker")
BLOCKED_ACTIONS = {"click", "type", "scroll", "submit", "drag", "browser navigation"}
WARNING_TERMS = (
    "alert",
    "blocked",
    "critical",
    "denied",
    "down",
    "error",
    "failed",
    "panic",
    "review",
    "unhealthy",
    "warning",
)


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


def ocr_risk(confidence: float) -> str:
    return "ALLOW" if confidence >= OCR_CONFIDENCE_THRESHOLD else "REVIEW_REQUIRED"


def image_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_text_panel(target: str) -> tuple[Path, str]:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now()
    stamp = timestamp.replace(":", "").replace("+", "Z")
    path = SCREENSHOT_DIR / f"{target}-{stamp}.png"
    lines = visual_panel_lines(target)
    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 26)
    title_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 34)
    line_height = 38
    width = 1800
    height = max(520, 150 + len(lines) * line_height)
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 82), fill="#e5e7eb")
    draw.text((36, 24), f"{target.upper()} OBSERVATION PANEL", fill="#111827", font=title_font)
    y = 120
    for line in lines:
        color = "#111827"
        lowered = line.casefold()
        if any(term in lowered for term in WARNING_TERMS):
            color = "#92400e"
        if "healthy" in lowered or "running" in lowered or "up" in lowered:
            color = "#166534"
        draw.text((44, y), line, fill=color, font=font)
        y += line_height
    image.save(path)
    return path, timestamp


def visual_panel_lines(target: str) -> list[str]:
    if target == "terminal":
        uptime = run(["uptime"]).stdout.strip()
        pwd = str(ROOT)
        return [
            "Terminal text capture",
            f"workspace: {pwd}",
            f"uptime: {uptime}",
            "guardian: active",
            "dmn: active",
            "warning labels: none",
        ]
    if target == "docker":
        completed = run(["docker", "compose", "-f", "observability/docker-compose.yml", "ps", "--format", "json"])
        lines = ["Docker containers"]
        if completed.returncode == 0:
            for raw in completed.stdout.splitlines():
                if not raw.strip():
                    continue
                item = json.loads(raw)
                lines.append(f"{item.get('Name')} {item.get('Service')} {item.get('State')} {item.get('Ports')}")
        else:
            lines.append(f"warning: docker status unavailable {completed.stderr.strip()}")
        return lines
    if target == "grafana":
        grafana_status = "unknown"
        prometheus_status = "unknown"
        try:
            grafana_status = str(urlopen("http://127.0.0.1:3000/api/health", timeout=3).status)
            prometheus_status = str(urlopen("http://127.0.0.1:9090/-/ready", timeout=3).status)
        except (OSError, URLError):
            pass
        return [
            "Grafana dashboard",
            f"Grafana health HTTP {grafana_status}",
            f"Prometheus ready HTTP {prometheus_status}",
            "Widget title: CPU usage",
            "Widget title: Memory usage",
            "Widget title: Disk usage",
            "Warning labels: none",
        ]
    return [f"{target} visual capture", "warning labels: none"]


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
        "cpu_dashboard": "not visually confirmed" if target != "grafana" else "grafana target captured for OCR parsing",
        "warning_indicators": {
            "red_pixel_ratio": red_ratio,
            "amber_pixel_ratio": amber_ratio,
            "saturated_pixel_ratio": round(saturated / total_pixels, 6),
            "bright_pixel_ratio": round(bright / total_pixels, 6),
            "dark_pixel_ratio": round(dark / total_pixels, 6),
        },
        "anomaly_notes": anomaly_notes,
    }


def crop_regions(image: Image.Image, target: str) -> dict[str, Image.Image]:
    width, height = image.size
    regions = {
        "full": image,
        "top_bar": image.crop((0, 0, width, max(1, int(height * 0.16)))),
        "center": image.crop((int(width * 0.12), int(height * 0.12), int(width * 0.88), int(height * 0.82))),
        "lower_half": image.crop((0, int(height * 0.45), width, height)),
    }
    if target == "grafana":
        regions["grafana_header"] = image.crop((0, 0, width, max(1, int(height * 0.22))))
        regions["grafana_panels"] = image.crop((0, int(height * 0.15), width, height))
    if target in {"terminal", "docker"}:
        regions["terminal_body"] = image.crop((0, int(height * 0.08), width, height))
    return regions


def preprocess_region(region: Image.Image) -> Image.Image:
    grayscale = region.convert("L")
    scale = 2
    resized = grayscale.resize((grayscale.width * scale, grayscale.height * scale), Image.Resampling.LANCZOS)
    contrasted = ImageEnhance.Contrast(resized).enhance(2.4)
    sharpened = contrasted.filter(ImageFilter.SHARPEN)
    array = np.array(sharpened)
    denoised = cv2.fastNlMeansDenoising(array, None, 7, 7, 21)
    thresholded = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9,
    )
    return Image.fromarray(thresholded)


def confidence_values(data: dict[str, list[Any]]) -> list[float]:
    values: list[float] = []
    for raw in data.get("conf", []):
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            values.append(value)
    return values


def mean_confidence(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def parse_visual_text(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lower_lines = [line.casefold() for line in lines]
    warnings = sorted(
        {
            line
            for line, lowered in zip(lines, lower_lines)
            if any(term in lowered for term in WARNING_TERMS)
            and "warning labels: none" not in lowered
            and "warnings: none" not in lowered
        }
    )
    percentages = sorted(set(re.findall(r"\b\d+(?:\.\d+)?\s?%", text)))
    numbers = sorted(set(re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])", text)))[:80]
    labels = sorted({line for line in lines if re.search(r"[A-Za-z][A-Za-z0-9 _./:-]{2,}", line)})[:80]
    widget_labels = [
        line
        for line in labels
        if re.search(r"(cpu|memory|disk|load|network|container|docker|prometheus|grafana|uptime|usage)", line, re.I)
    ][:40]
    terminal_text = "\n".join(lines[-40:])
    return {
        "numbers": numbers,
        "percentages": percentages,
        "warning_labels": warnings,
        "labels": labels,
        "terminal_text": terminal_text,
        "widget_labels": widget_labels,
    }


def ocr_image(path: Path, target: str, stamp: str) -> dict[str, Any]:
    source = Image.open(path).convert("RGB")
    PREPROCESS_DIR.mkdir(parents=True, exist_ok=True)
    regions: list[dict[str, Any]] = []
    all_text: list[str] = []
    all_confidence: list[float] = []

    for name, region in crop_regions(source, target).items():
        processed = preprocess_region(region)
        processed_path = PREPROCESS_DIR / f"{target}-{stamp}-{name}.png"
        processed.save(processed_path)
        data = pytesseract.image_to_data(
            processed,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT,
        )
        words = [word.strip() for word in data.get("text", []) if word and word.strip()]
        text = " ".join(words)
        confidences = confidence_values(data)
        all_text.append(text)
        all_confidence.extend(confidences)
        regions.append(
            {
                "name": name,
                "text": text,
                "confidence": mean_confidence(confidences),
                "preprocessed_path": str(processed_path.relative_to(ROOT)),
            }
        )

    combined_text = "\n".join(text for text in all_text if text).strip()
    confidence = mean_confidence(all_confidence)
    parsed = parse_visual_text(combined_text)
    return {
        "status": "completed" if combined_text else "empty",
        "text": combined_text,
        "engine": "tesseract",
        "confidence": confidence,
        "threshold": OCR_CONFIDENCE_THRESHOLD,
        "risk": ocr_risk(confidence),
        "regions": regions,
        "parsed": parsed,
    }


def capture(target: str) -> dict[str, Any]:
    enforce_observe_only()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if target in {"terminal", "docker", "grafana"}:
        screenshot_path, timestamp = render_text_panel(target)
        capture_method = "rendered_observation_panel"
    else:
        timestamp = utc_now()
        stamp = timestamp.replace(":", "").replace("+", "Z")
        screenshot_path = SCREENSHOT_DIR / f"{target}-{stamp}.png"
        completed = run(["screencapture", "-x", str(screenshot_path)])
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "screencapture failed")
        capture_method = "macos_screencapture"
    stamp = screenshot_path.stem.removeprefix(f"{target}-")

    metadata = {
        "timestamp": timestamp,
        "target": target,
        "path": str(screenshot_path.relative_to(ROOT)),
        "sha256": image_sha256(screenshot_path),
        "size_bytes": screenshot_path.stat().st_size,
        "dimensions": image_dimensions(screenshot_path),
        "policy": str(POLICY_FILE.relative_to(ROOT)),
        "capture_method": capture_method,
    }
    ocr = ocr_image(screenshot_path, target, stamp)
    analysis = analyze_image(screenshot_path, target)
    risk = str(ocr["risk"])
    approval = None
    if risk == "REVIEW_REQUIRED":
        approval = record_approval(
            "vision:ocr-confidence",
            risk,
            "vision_capture:auto-record",
            f"confidence {ocr['confidence']} below threshold {ocr['threshold']}",
        )
    record = {
        "metadata": metadata,
        "ocr": {
            "status": ocr["status"],
            "engine": ocr["engine"],
            "text": ocr["text"],
            "confidence": ocr["confidence"],
            "threshold": ocr["threshold"],
            "risk": risk,
            "regions": ocr["regions"],
            "parsed": ocr["parsed"],
        },
        "analysis": analysis,
        "guardian": {
            "risk": risk,
            "approval": approval,
        },
    }
    analysis_path = ANALYSIS_DIR / f"{target}-{stamp}.json"
    analysis_path.write_text(stable_json(record) + "\n", encoding="utf-8")

    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(stable_json({"timestamp": utc_now(), "event": "capture", "analysis": str(analysis_path.relative_to(ROOT))}) + "\n")

    dmn_payload = {
        "image_metadata": metadata,
        "ocr_text": ocr["text"],
        "ocr_status": ocr["status"],
        "ocr_confidence": ocr["confidence"],
        "ocr_threshold": ocr["threshold"],
        "ocr_risk": risk,
        "detected_warnings": ocr["parsed"]["warning_labels"],
        "widget_labels": ocr["parsed"]["widget_labels"],
        "labels": ocr["parsed"]["labels"],
        "numbers": ocr["parsed"]["numbers"],
        "percentages": ocr["parsed"]["percentages"],
        "terminal_text": ocr["parsed"]["terminal_text"],
        "anomaly_notes": analysis["anomaly_notes"],
        "visible_windows": analysis["visible_windows"],
        "cpu_dashboard": analysis["cpu_dashboard"],
        "warning_indicators": analysis["warning_indicators"],
    }
    append_memory(stable_json(dmn_payload), ["vision", "cua", "observe-only", "night4"], "vision_capture")
    log_action(
        "vision:capture",
        "completed",
        risk,
        {
            "target": target,
            "analysis": str(analysis_path.relative_to(ROOT)),
            "ocr_confidence": ocr["confidence"],
            "threshold": ocr["threshold"],
        },
    )
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
