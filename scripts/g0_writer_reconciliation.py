"""Reconcile caller-supplied synthetic observations; never inspect the host.

This module provides no collection adapter or gate decision.  Before/after are
caller-labelled samples, not proof of time ordering or complete observation.
All strings accepted by the input schema are fixed enums or SHA-256 identities.
"""

import json
import re

# Per sample/group limits exceed the documented 478-process, 306-service and
# 210-task inventory. Handle rows are observations, not distinct identities.
MAX_PROCESS_ROWS = 1024
MAX_SERVICE_ROWS = 512
MAX_TASK_ROWS = 512
MAX_HANDLE_ROWS = 2048
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
_SNAPSHOT_STATUS = {"COMPLETE", "INCOMPLETE", "ACCESS_DENIED", "TIMEOUT", "UNOBSERVABLE"}
_HANDLE_STATUS = {"POSITIVE", "EMPTY", "ACCESS_DENIED", "TIMEOUT", "NOT_PROBED", "ERROR"}
_STATES = {"RUNNING", "STOPPED", "READY", "DISABLED", "UNKNOWN"}
_TARGETS = {"DB", "WAL", "SHM", "OTHER_APPROVED"}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _invalid():
    # Never include caller-controlled data in exception text.
    raise ValueError("invalid or over-limit synthetic observation")


def _object(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        _invalid()


def _rows(value, limit):
    if type(value) is not list or len(value) > limit:
        _invalid()
    return value


def _number(value, *, optional=False):
    if optional and value is None:
        return
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        _invalid()


def _enum(value, allowed):
    if type(value) is not str or value not in allowed:
        _invalid()


def _snapshot(snapshot):
    _object(snapshot, ("processes", "services", "tasks"))
    for kind in ("processes", "services", "tasks"):
        group = snapshot[kind]
        _object(group, ("status", "rows"))
        _enum(group["status"], _SNAPSHOT_STATUS)
        seen = set()
        limit = {"processes": MAX_PROCESS_ROWS, "services": MAX_SERVICE_ROWS,
                 "tasks": MAX_TASK_ROWS}[kind]
        for row in _rows(group["rows"], limit):
            if kind == "processes":
                _object(row, ("pid", "created_ns", "candidate"))
                _number(row["pid"])
                _number(row["created_ns"], optional=True)
                if row["candidate"] is not None and type(row["candidate"]) is not bool:
                    _invalid()
                identity = row["pid"]
            else:
                _object(row, ("identity_sha256", "state", "pid", "created_ns", "candidate"))
                identity = row["identity_sha256"]
                if type(identity) is not str or not _SHA256.fullmatch(identity):
                    _invalid()
                _enum(row["state"], _STATES)
                _number(row["pid"], optional=True)
                _number(row["created_ns"], optional=True)
                if row["candidate"] is not None and type(row["candidate"]) is not bool:
                    _invalid()
            if identity in seen:
                _invalid()
            seen.add(identity)


def _handles(handles):
    for row in _rows(handles, MAX_HANDLE_ROWS):
        _object(row, ("pid", "created_ns", "identity_stable", "status", "target"))
        _number(row["pid"])
        _number(row["created_ns"], optional=True)
        if type(row["identity_stable"]) is not bool:
            _invalid()
        _enum(row["status"], _HANDLE_STATUS)
        if row["status"] == "POSITIVE":
            _enum(row["target"], _TARGETS)
        elif row["target"] is not None:
            _invalid()


def reconcile(before, after, handles):
    """Return bounded, redacted observations; writer closure is always UNKNOWN.

    Each snapshot contains processes/services/tasks groups with status and rows.
    Handles are independent observations and must not be inferred to be in the
    same observation window. Positive handles indicate possible writers only.
    """
    _snapshot(before)
    _snapshot(after)
    _handles(handles)
    b = {row["pid"]: row for row in before["processes"]["rows"]}
    a = {row["pid"]: row for row in after["processes"]["rows"]}
    complete = (before["processes"]["status"] == "COMPLETE" and
                after["processes"]["status"] == "COMPLETE")
    processes = []
    for pid in sorted(b.keys() | a.keys()):
        old, new = b.get(pid), a.get(pid)
        if old and new and old["created_ns"] is not None and new["created_ns"] is not None:
            if old["created_ns"] == new["created_ns"]:
                change = "OBSERVED_BOTH"
            else:
                change = "PID_REUSED_IF_ORDERED" if complete else "UNKNOWN"
        elif old and not new and old["created_ns"] is not None and complete:
            change = "EXITED_IF_ORDERED"
        elif new and not old and new["created_ns"] is not None and complete:
            change = "NEW_IF_ORDERED"
        else:
            change = "UNKNOWN"
        processes.append({"pid": pid, "before_created_ns": old["created_ns"] if old else None,
                          "after_created_ns": new["created_ns"] if new else None,
                          "before_candidate": old["candidate"] if old else None,
                          "after_candidate": new["candidate"] if new else None,
                          "observation": change})

    triggers = []
    for label, snapshot in (("BEFORE", before), ("AFTER", after)):
        index = {r["pid"]: r["created_ns"] for r in snapshot["processes"]["rows"]}
        for kind in ("services", "tasks"):
            for row in snapshot[kind]["rows"]:
                linked = (row["pid"] is not None and row["created_ns"] is not None and
                          row["pid"] in index and index[row["pid"]] == row["created_ns"])
                triggers.append({"sample": label, "kind": kind.upper(),
                                 "identity_sha256": row["identity_sha256"],
                                 "state": row["state"], "candidate": row["candidate"],
                                 "pid": row["pid"], "created_ns": row["created_ns"],
                                 "association": "EXACT_IDENTITY_IN_SAMPLE" if linked else "UNKNOWN"})

    observations = []
    for row in handles:
        bound = row["identity_stable"] and row["created_ns"] is not None
        observations.append({"pid": row["pid"], "created_ns": row["created_ns"],
                             "status": row["status"], "target": row["target"],
                             "finding": ("POSSIBLE_WRITER" if bound else "POSSIBLE_WRITER_IDENTITY_UNKNOWN")
                             if row["status"] == "POSITIVE" else "UNKNOWN"})
    result = {"writer_closure": "UNKNOWN", "time_order_verified": False,
              "handle_rows_semantics": "OBSERVATIONS_NOT_UNIQUE_HANDLES_OR_WRITERS",
              "snapshot_status": {label: {kind: snap[kind]["status"] for kind in
                                  ("processes", "services", "tasks")}
                                  for label, snap in (("before", before), ("after", after))},
              "processes": processes, "triggers": triggers, "handles": observations}
    if len(json.dumps(result, ensure_ascii=True, separators=(",", ":")).encode("ascii")) > MAX_OUTPUT_BYTES:
        _invalid()
    return result
