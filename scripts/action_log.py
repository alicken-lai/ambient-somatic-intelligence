#!/usr/bin/env python3
"""Structured append-only action log helpers."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / "logs" / "actions.jsonl"
CHECKSUM_FILE = ROOT / "logs" / "checksums.jsonl"
LOCK_FILE = ROOT / "logs" / ".checksum.lock"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(record: dict[str, Any]) -> str:
    return json.dumps(record, separators=(",", ":"), sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def append_jsonl(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = stable_json(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return record


@contextmanager
def checksum_lock():
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def last_chain_hash(path: Path = CHECKSUM_FILE) -> str:
    if not path.exists():
        return ""

    last = ""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            last = json.loads(line)["chain_hash"]
    return last


def record_checksum(target: Path, event: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    with checksum_lock():
        target = target.resolve()
        previous = last_chain_hash()
        payload = target.read_text(encoding="utf-8") if target.exists() else ""
        record = {
            "timestamp": utc_now(),
            "event": event,
            "target": str(target.relative_to(ROOT)),
            "target_sha256": sha256_text(payload),
            "previous_chain_hash": previous,
            "metadata": metadata or {},
        }
        record["chain_hash"] = sha256_text(stable_json(record))
        return append_jsonl(CHECKSUM_FILE, record)


def log_action(action: str, status: str, risk: str = "UNKNOWN", detail: dict[str, Any] | None = None) -> dict[str, Any]:
    record = {
        "timestamp": utc_now(),
        "action": action,
        "status": status,
        "risk": risk,
        "detail": detail or {},
    }
    append_jsonl(LOG_FILE, record)
    record_checksum(LOG_FILE, "action_log_append", {"action": action, "status": status})
    return record


def verify_checksum_chain(path: Path = CHECKSUM_FILE) -> tuple[bool, str]:
    previous = ""
    latest_by_target: dict[str, str] = {}
    if not path.exists():
        return True, "no checksum records"

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            chain_hash = record.pop("chain_hash")
            if record["previous_chain_hash"] != previous:
                return False, f"broken previous hash at line {line_number}"
            if sha256_text(stable_json(record)) != chain_hash:
                return False, f"broken chain hash at line {line_number}"
            latest_by_target[record["target"]] = record["target_sha256"]
            previous = chain_hash
    for target_name, expected_hash in latest_by_target.items():
        target = ROOT / target_name
        if target.exists() and sha256_text(target.read_text(encoding="utf-8")) != expected_hash:
            return False, f"target changed since latest checksum: {target_name}"
    return True, "checksum chain valid"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write and verify structured action logs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("action")
    log_parser.add_argument("status")
    log_parser.add_argument("--risk", default="UNKNOWN")
    log_parser.add_argument("--detail", default="{}")

    checksum_parser = subparsers.add_parser("checksum")
    checksum_parser.add_argument("target")
    checksum_parser.add_argument("--event", default="manual_checksum")

    subparsers.add_parser("verify")

    args = parser.parse_args()
    if args.command == "log":
        detail = json.loads(args.detail)
        print(stable_json(log_action(args.action, args.status, args.risk, detail)))
        return 0
    if args.command == "checksum":
        print(stable_json(record_checksum(ROOT / args.target, args.event)))
        return 0

    ok, message = verify_checksum_chain()
    print(json.dumps({"ok": ok, "message": message}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
