from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path

import pytest


def load(name):
    path = Path(__file__).parents[1] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


snapshot = load("mother_dmn_snapshot")
proposal = load("prepare_mother_cron_bounded")
NOW = datetime(2026, 11, 10, tzinfo=timezone.utc)


def test_real_failure_shape_is_bounded(tmp_path):
    path = tmp_path / "dmn.jsonl"
    records = [{"timestamp": (NOW - timedelta(minutes=i)).isoformat(),
                "content": "記憶與真誠好奇" * 20000} for i in range(12)]
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in records), encoding="utf-8")
    value = snapshot.collect(path, NOW)
    assert value["status"] == "ok"
    assert len(value["records"]) <= 5
    assert len((snapshot._encode(value) + "\n").encode("utf-8")) <= 2400
    assert snapshot._encode(value).isascii()
    assert all(len(x["excerpt"].encode("utf-8")) <= 300 for x in value["records"])


def test_time_filter_order_and_invalid_records(tmp_path):
    path = tmp_path / "dmn.jsonl"
    items = [{"timestamp": (NOW - timedelta(hours=h)).isoformat(), "content": str(h)}
             for h in (1, 30, 0, -1, 2, 3, 4, 5, 6)]
    path.write_text("bad\n" + "\n".join(json.dumps(x) for x in items), encoding="utf-8")
    value = snapshot.collect(path, NOW)
    assert [x["excerpt"] for x in value["records"]] == ["0", "1", "2", "3", "4"]
    assert value["invalid_records"] == 1


def test_missing_empty_and_oversized(tmp_path):
    path = tmp_path / "dmn.jsonl"
    assert snapshot.collect(path, NOW)["status"] == "DMN_UNAVAILABLE"
    path.write_bytes(b"x" * (snapshot.MAX_LINE_BYTES + 10) + b"\n")
    value = snapshot.collect(path, NOW)
    assert value["status"] == "no_recent_memory"
    assert value["oversized_records_skipped"] == 1


def test_redaction_before_excerpt(tmp_path):
    path = tmp_path / "dmn.jsonl"
    content = "Bearer abcdef api_key=topsecret freellmapi-abcdefghijkl person@example.com"
    path.write_text(json.dumps({"timestamp": NOW.isoformat(), "content": content}), encoding="utf-8")
    text = snapshot._encode(snapshot.collect(path, NOW))
    assert all(s not in text for s in ("abcdef", "topsecret", "person@example.com"))


def test_quoted_credentials_and_timezone_offsets(tmp_path):
    path = tmp_path / "dmn.jsonl"
    record = {"timestamp": "2026-11-10T08:00:00+08:00",
              "content": 'api_key="two word secret" token=hidden github_pat_' + 'a' * 30}
    path.write_text(json.dumps(record), encoding="utf-8")
    value = snapshot.collect(path, NOW)
    text = snapshot._encode(value)
    assert value["status"] == "ok"
    assert all(s not in text for s in ("word secret", "hidden", "a" * 30))


def test_job_proposal_preserves_history_other_jobs_and_settings():
    before = {"version": 7, "jobs": [
        {"id": proposal.JOB_ID, "provider": "custom:freellmapi", "model": "auto",
         "last_error": "retained 413", "deliver": "origin", "enabled": True,
         "schedule": {"cron": "30 4 * * 0"}},
        {"id": "other", "prompt": "preserved"}]}
    after = json.loads(proposal.prepare(json.dumps(before).encode()))
    expected = json.loads(json.dumps(before))
    expected["jobs"][0].update(script=proposal.SCRIPT, prompt=proposal.PROMPT, enabled_toolsets=["todo"])
    assert after == expected


@pytest.mark.parametrize("change", [{"provider": "other"}, {"script": "existing.py"}, {"no_agent": True}])
def test_proposal_rejects_unexpected_state(change):
    job = {"id": proposal.JOB_ID, "provider": "custom:freellmapi", "model": "auto", **change}
    with pytest.raises(ValueError):
        proposal.prepare(json.dumps({"jobs": [job]}).encode())
