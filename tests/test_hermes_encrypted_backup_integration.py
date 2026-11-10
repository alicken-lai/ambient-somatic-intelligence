"""Real synthetic SQLite/child integration; never opens operator databases."""
import contextlib
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import tracemalloc
import unittest
from unittest.mock import patch
import zipfile

from scripts import hermes_encrypted_backup as backup


KEY = bytes(range(32))


class BackupIntegrationTests(unittest.TestCase):
    def setUp(self):
        # The desktop sandbox's redirected system TEMP can create directories
        # that SQLite cannot reopen. Keep all disposable fixtures in workspace.
        test_parent = Path(__file__).resolve().parents[1] / ".staging"
        test_parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="asi-synthetic-backup-", dir=test_parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def database(self, *, wal=False, large_bytes=0):
        path = self.root / "synthetic.sqlite"
        connection = sqlite3.connect(path)
        if wal:
            connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript("""
            PRAGMA user_version=19;
            PRAGMA foreign_keys=ON;
            CREATE TABLE parent(id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id), value BLOB);
            CREATE INDEX child_parent ON child(parent_id);
            CREATE TABLE audit(value TEXT);
            CREATE TRIGGER child_insert AFTER INSERT ON child BEGIN INSERT INTO audit VALUES ('inserted'); END;
            CREATE VIRTUAL TABLE search USING fts5(text);
            INSERT INTO parent VALUES(1, 'synthetic');
            INSERT INTO child VALUES(1, 1, X'001122');
            INSERT INTO search VALUES('synthetic searchable text');
        """)
        if large_bytes:
            connection.execute("CREATE TABLE capacity(value BLOB)")
            connection.execute("INSERT INTO capacity VALUES(zeroblob(?))", (large_bytes,))
        connection.commit()
        return path, connection

    def decrypt_report(self, path, report):
        return backup.decrypt_bytes(path, KEY, expected_format=report["payload_format"],
            expected_ciphertext_sha256=report["ciphertext_sha256"],
            expected_plaintext_sha256=report["plaintext_sha256"],
            expected_plaintext_bytes=report["plaintext_bytes"])

    def test_actual_sqlite_backup_restore_fts_fk_and_source_preservation(self):
        source, connection = self.database()
        connection.close()
        before = backup.sha256_file(source)
        target = self.root / "synthetic.heb"
        report = backup.sqlite_backup(source, target, KEY)
        self.assertEqual(report["payload_format"], "HEB2")
        self.assertEqual(report["encrypted_restore_smoke"], "ok")
        self.assertEqual(before, backup.sha256_file(source))
        restored = self.root / "synthetic-restored.sqlite"
        with restored.open("xb") as stream:
            stream.write(self.decrypt_report(target, report))
        check = sqlite3.connect(restored.as_uri() + "?mode=ro", uri=True)
        try:
            self.assertEqual(check.execute("SELECT * FROM child").fetchall(), [(1, 1, b"\0\x11\x22")])
            self.assertEqual(check.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(check.execute("SELECT count(*) FROM search WHERE search MATCH 'searchable'").fetchone(), (1,))
            self.assertEqual(check.execute("SELECT * FROM audit").fetchall(), [("inserted",)])
        finally:
            check.close()
        with self.assertRaises(FileExistsError):
            backup.sqlite_backup(source, target, KEY)

    def test_actual_wal_sqlite_backup_normalizes_only_verification_copy(self):
        source, connection = self.database(wal=True)
        self.addCleanup(connection.close)
        report = backup.sqlite_backup(source, self.root / "wal.heb", KEY)
        self.assertTrue(report["restore_header_normalized_from_wal"])
        raw = self.decrypt_report(self.root / "wal.heb", report)
        self.assertEqual(raw[18:20], b"\x02\x02")
        self.assertEqual(connection.execute("SELECT count(*) FROM child").fetchone(), (1,))

    def test_capacity_and_memory_admission_before_encrypted_output(self):
        source, connection = self.database()
        connection.close()
        target = self.root / "rejected.heb"
        with self.assertRaisesRegex(ValueError, "operation limit"):
            backup.sqlite_backup(source, target, KEY, max_plaintext_bytes=4096)
        self.assertFalse(target.exists())
        with self.assertRaisesRegex(ValueError, "memory budget"):
            backup.sqlite_backup(source, target, KEY, memory_budget_bytes=16 * 1024**2)
        self.assertFalse(target.exists())

    def test_command_drains_stderr_above_pipe_capacity(self):
        target = self.root / "command.heb"
        code = "import sys; sys.stderr.buffer.write(b'E'*200000); sys.stderr.flush(); sys.stdout.buffer.write(b'S'*200000)"
        report = backup.encrypt_command([sys.executable, "-I", "-S", "-c", code], self.root, target, KEY,
                                        timeout_seconds=10)
        self.assertEqual(report["stderr_bytes"], 200000)
        self.assertTrue(report["capture_readers_joined"])
        self.assertEqual(self.decrypt_report(target, report), b"S" * 200000)

    def test_command_timeout_stderr_limit_and_nonzero_refuse_success(self):
        cases = [("import time; time.sleep(10)", {"timeout_seconds": .2}),
                 ("import sys; sys.stderr.buffer.write(b'E'*200000)", {"max_stderr_bytes": 100}),
                 ("raise SystemExit(3)", {})]
        for index, (code, options) in enumerate(cases):
            started = time.monotonic()
            with self.subTest(index=index), self.assertRaises((RuntimeError, subprocess_timeout())):
                backup.encrypt_command([sys.executable, "-I", "-S", "-c", code], self.root,
                    self.root / f"failure-{index}.heb", KEY, **options)
            self.assertLess(time.monotonic() - started, 6)

    def manifest_fixture(self, version="HEB2", extra_home=None):
        home = self.root / "synthetic-home"
        home.mkdir()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as stream:
            stream.writestr("synthetic.txt", "synthetic source")
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE synthetic(value INTEGER)")
        db.execute("INSERT INTO synthetic VALUES(42)")
        db.commit()
        db_report = backup.inspect_db(db)
        db_image = db.serialize()
        db.close()
        raw = [("source-capture", "head.zip", archive.getvalue()),
               ("hermes-agent-dirty-file", "synthetic.py", b"pass\n"),
               ("hermes-home-file", "config.yaml", b"synthetic: true\n"),
               ("hermes-home-file", ".env", b"SYNTHETIC=fixture\n"),
               ("sqlite-online-backup", "synthetic.sqlite", db_image),
               ("git-recovery-metadata", "git.remote-v", b"synthetic remote\n"),
               ("git-recovery-metadata", "git.ignored-path-map", b"")]
        raw.extend(("hermes-home-file", logical, value) for logical, value in (extra_home or {}).items())
        items = []
        for index, (category, logical, value) in enumerate(raw):
            if category in {"hermes-home-file", "sqlite-online-backup"}:
                source_path = home / logical
                source_path.parent.mkdir(parents=True, exist_ok=True)
                source_path.write_bytes(value)
            object_path = self.root / f"object-{index}.heb"
            report = backup.encrypt_stream(io.BytesIO(value), object_path, KEY, format_version=version)
            if category == "sqlite-online-backup":
                report.update(db_report)
            report_path = self.root / f"report-{index}.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            item = dict(category=category, relative_path=logical, backup_object=object_path.name,
                verification_report=report_path.name,
                **{key: report[key] for key in ("plaintext_bytes", "plaintext_sha256", "ciphertext_bytes", "ciphertext_sha256", "payload_format")})
            if category == "hermes-home-file":
                item.update(source_acl_sddl="synthetic-acl", source_acl_sddl_sha256=hashlib.sha256(b"synthetic-acl").hexdigest())
            if category == "sqlite-online-backup":
                item["source_relative_path"] = logical
            items.append(item)
        filtered = self.root / "filtered.json"
        filtered.write_text(json.dumps(dict(maximum_entries=10, source_count=0, entries=[], decision_counts={})))
        source_inventory = backup.inventory_home(home)
        for entry in [source_inventory, *source_inventory["entries"]]:
            if entry is source_inventory or entry["disposition"] in {"keep_encrypted", "preserve_directory"}:
                entry.update(source_acl_sddl="synthetic-acl", source_acl_sddl_sha256=hashlib.sha256(b"synthetic-acl").hexdigest())
        source_inventory_path = self.root / "home-source-inventory.json"
        source_inventory_path.write_text(json.dumps(source_inventory), encoding="utf-8")
        manifest = dict(schema="hermes-upgrade-backup-manifest/v4", items=items,
            home_source_inventory=dict(path=source_inventory_path.name, sha256=backup.sha256_file(source_inventory_path)),
            recovery=dict(key_owner_sid="synthetic"), exact_targets=dict(hermes_home=str(home)),
            source_git_metadata=dict(remote_v_hashes=[hashlib.sha256(b"synthetic remote").hexdigest()],
                secret_filtered_ignored_inventory=filtered.name,
                secret_filtered_ignored_inventory_sha256=backup.sha256_file(filtered), ignored_decision_counts={}))
        path = self.root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path, backup.sha256_file(path)

    def test_trusted_manifest_and_full_synthetic_run(self):
        manifest, expected = self.manifest_fixture()
        with patch.object(backup, "_make_private_restore_root") as make_root:
            with self.assertRaisesRegex(ValueError, "manifest hash"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256="0" * 64)
            make_root.assert_not_called()
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", return_value="synthetic"):
            result = backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["manifest_sha256"], expected)
        self.assertEqual(result["legacy_heb1_items"], 0)

    def test_legacy_run_requires_opt_in_and_pinned_manifest(self):
        manifest, expected = self.manifest_fixture("HEB1")
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", return_value="synthetic"):
            with self.assertRaisesRegex(ValueError, "not admitted"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
            result = backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected,
                                       allow_legacy_heb1=True)
        self.assertEqual(result["legacy_heb1_items"], 7)

    def test_legacy_without_source_inventory_reports_coverage_unknown(self):
        manifest, _ = self.manifest_fixture("HEB1")
        payload = json.loads(manifest.read_text())
        del payload["home_source_inventory"]
        manifest.write_text(json.dumps(payload))
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", return_value="synthetic"):
            result = backup.verify_run(self.root, manifest, KEY,
                expected_manifest_sha256=backup.sha256_file(manifest), allow_legacy_heb1=True)
        self.assertEqual(result["status"], "legacy_payloads_verified_coverage_unknown")
        self.assertFalse(result["home_source_coverage"]["complete"])

    def test_source_inventory_covers_root_credentials_memories_custom_launchers_and_old_configs(self):
        extra = {"auth.json": b'{"synthetic":true}', "memories/MEMORY.md": b"synthetic memory",
                 "SOUL.md": b"synthetic", "gateway-service/launch.cmd": b"synthetic",
                 "channel_directory.json": b"{}", "gateway_state.json": b"{}",
                 "bin/synthetic.exe": b"not executable", "hooks/synthetic.py": b"pass",
                 ".env.bak-copilot-quota-20260615": b"SYNTHETIC=old",
                 "config.yaml.bak-rate-limit-20260616-144830": b"synthetic: old",
                 "unknown-new-directory/value.json": b"{}"}
        manifest, expected = self.manifest_fixture(extra_home=extra)
        def check_empty_witness(path, _sddl):
            self.assertEqual(path.read_bytes(), b"")
            return "synthetic"
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", side_effect=check_empty_witness):
            result = backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
        self.assertEqual(result["home_source_coverage"]["required_files"], len(extra) + 2)
        self.assertTrue(result["home_source_coverage"]["source_remeasured"])
        self.assertEqual(result["distinct_file_acl_restore_checks"], 1)
        self.assertFalse(result["credential_or_config_plaintext_persisted"])

    def test_omitted_auth_and_memories_objects_are_rejected(self):
        manifest, _ = self.manifest_fixture(extra_home={"auth.json": b"{}", "memories/MEMORY.md": b"synthetic"})
        payload = json.loads(manifest.read_text())
        payload["items"] = [item for item in payload["items"] if item.get("relative_path") not in {"auth.json", "memories/MEMORY.md"}]
        manifest.write_text(json.dumps(payload))
        with patch.object(backup, "_make_private_restore_root") as make_root:
            with self.assertRaisesRegex(ValueError, "not backed up"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=backup.sha256_file(manifest))
            make_root.assert_not_called()

    def test_new_source_file_missing_from_inventory_is_rejected(self):
        manifest, expected = self.manifest_fixture()
        (self.root / "synthetic-home" / "auth.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "current home source inventory"):
            backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)

    def test_filtered_inventory_sidecar_cannot_escape_run_root(self):
        manifest, _ = self.manifest_fixture()
        payload = json.loads(manifest.read_text())
        payload["source_git_metadata"]["secret_filtered_ignored_inventory"] = "../outside-filtered.json"
        manifest.write_text(json.dumps(payload))
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", return_value="synthetic"):
            with self.assertRaisesRegex(ValueError, "escapes run root"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=backup.sha256_file(manifest))

    def test_source_inventory_sidecar_cannot_escape_run_root(self):
        manifest, _ = self.manifest_fixture()
        payload = json.loads(manifest.read_text())
        payload["home_source_inventory"]["path"] = "../outside-inventory.json"
        manifest.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "escapes run root"):
            backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=backup.sha256_file(manifest))

    def test_inventory_excludes_subtrees_before_traversal_and_records_transients(self):
        home = self.root / "inventory-home"
        home.mkdir()
        for name in ("backups", "logs", "cache", "hermes-agent"):
            (home / name).mkdir()
            (home / name / "must-not-be-traversed").mkdir()
        (home / "gateway.pid").write_bytes(b"synthetic")
        (home / "auth.lock").write_bytes(b"synthetic")
        (home / "auth.json").write_bytes(b"{}")
        actual_scandir = backup.os.scandir
        def guarded_scandir(path):
            self.assertEqual(Path(path), home)
            return actual_scandir(path)
        with patch.object(backup.os, "scandir", side_effect=guarded_scandir):
            inventory = backup.inventory_home(home)
        dispositions = {entry["relative_path"]: entry["disposition"] for entry in inventory["entries"]}
        self.assertEqual(dispositions["auth.json"], "keep_encrypted")
        self.assertEqual(dispositions["gateway.pid"], "exclude_transient")
        self.assertEqual(dispositions["auth.lock"], "exclude_transient")
        self.assertTrue(all(dispositions[name] == "exclude_subtree" for name in ("backups", "logs", "cache", "hermes-agent")))

    def test_mutable_report_cannot_replace_manifest_payload_pins(self):
        manifest, expected = self.manifest_fixture()
        report_path = self.root / "report-0.json"
        report = json.loads(report_path.read_text())
        report["ciphertext_sha256"] = "0" * 64
        report_path.write_text(json.dumps(report))
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()):
            with self.assertRaisesRegex(ValueError, "pins"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)

    def test_trusted_manifest_still_cannot_escape_run_root(self):
        manifest, _expected = self.manifest_fixture()
        payload = json.loads(manifest.read_text())
        payload["items"][0]["backup_object"] = ".."
        manifest.write_text(json.dumps(payload))
        expected = backup.sha256_file(manifest)
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()):
            with self.assertRaisesRegex(ValueError, "escapes"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)

    def test_exclusive_witness_collision_preserves_foreign_file(self):
        manifest, expected = self.manifest_fixture()
        foreign = self.root / "isolated-acl-restore" / (hashlib.sha256(b"synthetic-acl").hexdigest() + ".tmp")
        def create_with_collision(path, _sid):
            path.mkdir()
            foreign.write_bytes(b"FOREIGN_FILE_MUST_SURVIVE")
        with patch.object(backup, "_make_private_restore_root", side_effect=create_with_collision), \
             patch.object(backup, "_apply_and_compare_windows_acl") as apply_acl, \
             patch.object(Path, "unlink", side_effect=AssertionError("verifier must not delete")):
            with self.assertRaisesRegex(RuntimeError, "UNKNOWN"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
            apply_acl.assert_not_called()
        self.assertEqual(foreign.read_bytes(), b"FOREIGN_FILE_MUST_SURVIVE")

    def test_unexpected_witness_directory_entry_is_retained_and_blocks(self):
        manifest, expected = self.manifest_fixture()
        foreign = self.root / "isolated-acl-restore" / "foreign.txt"
        def inject_unknown(path, _sddl):
            foreign.write_bytes(b"FOREIGN_FILE_MUST_SURVIVE")
            return "synthetic"
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", side_effect=inject_unknown), \
             patch.object(Path, "unlink", side_effect=AssertionError("verifier must not delete")):
            with self.assertRaisesRegex(RuntimeError, "UNKNOWN"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
        self.assertEqual(foreign.read_bytes(), b"FOREIGN_FILE_MUST_SURVIVE")

    def test_acl_exception_retains_owned_empty_witness_without_plaintext(self):
        manifest, expected = self.manifest_fixture()
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", side_effect=RuntimeError("synthetic ACL failure")), \
             patch.object(Path, "unlink", side_effect=AssertionError("verifier must not delete")):
            with self.assertRaisesRegex(RuntimeError, "synthetic ACL failure"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
        witnesses = list((self.root / "isolated-acl-restore").iterdir())
        self.assertEqual(len(witnesses), 1)
        self.assertEqual(witnesses[0].read_bytes(), b"")

    def test_witness_identity_change_is_retained_and_blocks(self):
        from types import SimpleNamespace
        import stat
        manifest, expected = self.manifest_fixture()
        actual_lstat = Path.lstat
        def changed_identity(path):
            observed = actual_lstat(path)
            if path.suffix == ".tmp":
                return SimpleNamespace(st_mode=stat.S_IFREG, st_dev=observed.st_dev,
                                       st_ino=observed.st_ino + 1, st_size=0, st_file_attributes=0)
            return observed
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", return_value="synthetic"), \
             patch.object(Path, "lstat", changed_identity), \
             patch.object(Path, "unlink", side_effect=AssertionError("verifier must not delete")):
            with self.assertRaisesRegex(RuntimeError, "UNKNOWN"):
                backup.verify_run(self.root, manifest, KEY, expected_manifest_sha256=expected)
        self.assertTrue(any((self.root / "isolated-acl-restore").iterdir()))

    @unittest.skipUnless(os.environ.get("ASI_RUN_LARGE_BACKUP_TEST") == "1", "explicit 75 MB synthetic capacity run")
    def test_historical_scale_actual_sqlite_backup_restore(self):
        source, connection = self.database(large_bytes=75_776_000)
        connection.close()
        tracemalloc.start()
        started = time.monotonic()
        report = backup.sqlite_backup(source, self.root / "capacity.heb", KEY)
        _current, python_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        evidence = dict(synthetic_only=True, source_bytes=source.stat().st_size,
            plaintext_bytes=report["plaintext_bytes"], payload_format=report["payload_format"],
            estimated_memory_bytes=report["estimated_memory_bytes"], memory_budget_bytes=report["memory_budget_bytes"],
            python_tracemalloc_peak_bytes=python_peak, elapsed_seconds=round(time.monotonic()-started, 3),
            os_hard_memory_limit_verified=False)
        if os.name == "nt":
            from ctypes import wintypes
            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                    (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            get_current = ctypes.windll.kernel32.GetCurrentProcess
            get_current.restype = ctypes.c_void_p
            query = ctypes.windll.psapi.GetProcessMemoryInfo
            query.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), wintypes.DWORD]
            query.restype = wintypes.BOOL
            if query(get_current(), ctypes.byref(counters), counters.cb):
                evidence["process_peak_working_set_bytes"] = counters.PeakWorkingSetSize
        print("SYNTHETIC_CAPACITY_EVIDENCE=" + json.dumps(evidence, sort_keys=True))
        self.assertGreaterEqual(report["plaintext_bytes"], 75_776_000)
        self.assertEqual(report["encrypted_restore_smoke"], "ok")
        self.assertLessEqual(report["estimated_memory_bytes"], report["memory_budget_bytes"])


def subprocess_timeout():
    import subprocess
    return subprocess.TimeoutExpired


if __name__ == "__main__":
    unittest.main()
