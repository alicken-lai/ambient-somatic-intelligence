"""Explicit historical-only verification using exclusively synthetic artifacts.

Windows ACL/DPAPI interfaces are mocked, not certified. Encryption, trusted
pins, contained sidecar mapping and in-memory SQLite restoration are real.
"""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

from cryptography.exceptions import InvalidTag

from scripts import hermes_encrypted_backup as backup
from tests import test_hermes_encrypted_backup_integration as fixtures

KEY = fixtures.KEY


class CapturedVerificationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BackupIntegrationTests(methodName="test_trusted_manifest_and_full_synthetic_run")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.original_root = self.fixture.root
        self.original_manifest, self.expected = self.fixture.manifest_fixture()
        self.root = self.original_root / "isolated-synthetic-copy"
        self.root.mkdir()
        # Copy only the synthetic captured artifacts, not the live source home.
        for source in self.original_root.iterdir():
            if source.is_file():
                shutil.copyfile(source, self.root / source.name)
        self.manifest = self.root / self.original_manifest.name
        self.home = self.original_root / "synthetic-home"

    def rewrite_manifest(self, mutate):
        value = json.loads(self.manifest.read_bytes())
        mutate(value)
        self.manifest.write_text(json.dumps(value), encoding="utf-8")
        self.expected = backup.sha256_file(self.manifest)

    @contextlib.contextmanager
    def mocked_acl(self):
        with patch.object(backup, "_make_private_restore_root", side_effect=lambda path, _sid: path.mkdir()), \
             patch.object(backup, "_apply_and_compare_windows_acl", return_value="synthetic"):
            yield

    def verify(self, **kwargs):
        with self.mocked_acl():
            return backup.verify_captured(self.root, self.manifest, KEY,
                expected_manifest_sha256=self.expected, **kwargs)

    def assert_historical_scope(self, result):
        self.assertIs(result["historical_only"], True)
        self.assertEqual(result["verification_scope"], "historical_capture_only")
        self.assertEqual(result["live_coverage"], "UNKNOWN")
        self.assertIs(result["live_source_observed"], False)
        self.assertEqual(result["point_in_time_coherence"], "NOT_ESTABLISHED")
        self.assertIs(result["gate_pass"], False)

    def test_unchanged_capture_restores_without_any_live_inventory_probe(self):
        actual_exists = Path.exists
        def forbid_source_exists(path):
            if path == self.home:
                raise AssertionError("live source must not be probed")
            return actual_exists(path)
        with patch.object(Path, "exists", forbid_source_exists), \
             patch.object(backup, "inventory_home", side_effect=AssertionError("live inventory forbidden")):
            result = self.verify()
        self.assert_historical_scope(result)
        self.assertEqual(result["status"], "historical_capture_verified")
        self.assertEqual(result["sqlite_integrity_schema_user_version"], "ok")
        self.assertEqual(result["home_source_coverage"]["state"], "CAPTURED_INVENTORY_COVERED")
        self.assertIs(result["home_source_coverage"]["source_remeasured"], False)
        self.assertFalse(result["credential_or_config_plaintext_persisted"])

    def test_current_drift_is_unknown_in_captured_mode_but_still_blocks_full_mode(self):
        (self.home / "auth.json").write_bytes(b'{"synthetic_added_after_capture":true}')
        with patch.object(backup, "_make_private_restore_root") as make_root:
            with self.assertRaisesRegex(ValueError, "current home source inventory"):
                backup.verify_run(self.root, self.manifest, KEY, expected_manifest_sha256=self.expected)
            make_root.assert_not_called()
        self.assert_historical_scope(self.verify())

    def test_original_manifest_and_locator_are_not_rewritten_to_hide_source(self):
        original_bytes = self.original_manifest.read_bytes()
        copied_bytes = self.manifest.read_bytes()
        result = self.verify()
        self.assertEqual(original_bytes, copied_bytes)
        self.assertEqual(self.original_manifest.read_bytes(), original_bytes)
        self.assertEqual(self.manifest.read_bytes(), copied_bytes)
        self.assertEqual(result["manifest_sha256"], backup.sha256_file(self.original_manifest))
        self.assertEqual(json.loads(copied_bytes)["exact_targets"]["hermes_home"], str(self.home))
        self.assertFalse((self.original_root / "isolated-acl-restore").exists())

    def test_unreachable_historical_locator_is_never_accessed(self):
        self.rewrite_manifest(lambda data: data["exact_targets"].update(
            hermes_home="Z:/synthetic-not-a-real-source/SYNTHETIC_SECRET"))
        with patch.object(backup, "inventory_home", side_effect=AssertionError("forbidden")):
            self.assert_historical_scope(self.verify())

    def test_wrong_trusted_manifest_hash_refuses_before_restore_root(self):
        with patch.object(backup, "_make_private_restore_root") as make_root:
            with self.assertRaisesRegex(ValueError, "manifest hash"):
                backup.verify_captured(self.root, self.manifest, KEY, expected_manifest_sha256="0" * 64)
            make_root.assert_not_called()

    def test_missing_required_captured_credential_still_refuses(self):
        self.rewrite_manifest(lambda data: data.update(items=[item for item in data["items"]
            if not (item["category"] == "hermes-home-file" and item["relative_path"] == ".env")]))
        with patch.object(backup, "_make_private_restore_root") as make_root:
            with self.assertRaisesRegex(ValueError, "not backed up"):
                backup.verify_captured(self.root, self.manifest, KEY,
                    expected_manifest_sha256=self.expected)
            make_root.assert_not_called()

    def test_missing_required_inventory_is_not_offline_success(self):
        self.rewrite_manifest(lambda data: data.pop("home_source_inventory"))
        with self.assertRaisesRegex(ValueError, "inventory is missing"):
            self.verify()

    def test_inventory_still_requires_trusted_sidecar_pin(self):
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "sidecar hash mismatch"):
            self.verify()

    def test_inventory_acl_mapping_is_still_required(self):
        inventory_path = self.root / "home-source-inventory.json"
        value = json.loads(inventory_path.read_bytes())
        value["source_acl_sddl_sha256"] = "0" * 64
        inventory_path.write_text(json.dumps(value), encoding="utf-8")
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(
            sha256=backup.sha256_file(inventory_path)))
        with self.assertRaisesRegex(ValueError, "ACL metadata"):
            self.verify()

    def test_captured_inventory_reference_cannot_escape_copy(self):
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(path="../home-source-inventory.json"))
        with self.assertRaisesRegex(ValueError, "escapes run root"):
            self.verify()

    def test_filtered_sidecar_reference_cannot_escape_copy(self):
        self.rewrite_manifest(lambda data: data["source_git_metadata"].update(
            secret_filtered_ignored_inventory="../filtered.json"))
        with self.assertRaisesRegex(ValueError, "escapes run root"):
            self.verify()

    def test_corrupt_ciphertext_is_not_captured_success(self):
        path = self.root / "object-0.heb"
        value = bytearray(path.read_bytes())
        value[-1] ^= 1
        path.write_bytes(value)
        with self.assertRaises(InvalidTag):
            self.verify()

    def test_untrusted_mutable_report_cannot_replace_manifest_payload_pin(self):
        path = self.root / "report-0.json"
        value = json.loads(path.read_bytes())
        value["plaintext_sha256"] = "0" * 64
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "pins"):
            self.verify()

    def test_actual_in_memory_sqlite_report_mismatch_refuses(self):
        path = self.root / "report-4.json"
        value = json.loads(path.read_bytes())
        value["user_version"] += 1
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "SQLite report mismatch"):
            self.verify()

    def use_legacy_fixture(self):
        # New synthetic root; the previous source/copy remains untouched.
        self.fixture.root = self.original_root / "synthetic-legacy"
        self.fixture.root.mkdir()
        self.root = self.fixture.root
        self.manifest, self.expected = self.fixture.manifest_fixture("HEB1")

    def test_legacy_reader_still_requires_explicit_opt_in(self):
        self.use_legacy_fixture()
        with self.assertRaisesRegex(ValueError, "not admitted"):
            self.verify()
        result = self.verify(allow_legacy_heb1=True)
        self.assertEqual(result["legacy_heb1_items"], 7)
        self.assert_historical_scope(result)

    def test_legacy_missing_trusted_full_hash_is_not_invented(self):
        self.use_legacy_fixture()
        self.rewrite_manifest(lambda data: data["items"][0].pop("plaintext_sha256"))
        with self.assertRaisesRegex(ValueError, "pins"):
            self.verify(allow_legacy_heb1=True)

    def test_legacy_missing_inventory_cannot_claim_captured_coverage(self):
        self.use_legacy_fixture()
        self.rewrite_manifest(lambda data: data.pop("home_source_inventory"))
        result = self.verify(allow_legacy_heb1=True)
        self.assertEqual(result["status"], "historical_payloads_verified_coverage_unknown")
        self.assertFalse(result["home_source_coverage"]["complete"])
        self.assert_historical_scope(result)

    def invoke_cli(self, report):
        argv = ["synthetic-backup", "verify-captured", "--key-file", "synthetic-key",
            "--manifest", str(self.manifest), "--run-root", str(self.root),
            "--report", str(report), "--expected-manifest-sha256", self.expected]
        output, error = io.StringIO(), io.StringIO()
        with self.mocked_acl(), patch.object(sys, "argv", argv), \
             patch.object(backup, "load_key", return_value=KEY), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = backup.main()
        return code, output.getvalue(), error.getvalue()

    def test_cli_success_explicitly_reports_historical_only_never_gate_pass(self):
        report = self.root / "captured-result.json"
        code, output, error = self.invoke_cli(report)
        self.assertEqual(code, 0)
        self.assertIn("completed_historical_only_gate_pass_false", output)
        self.assertEqual(error, "")
        self.assert_historical_scope(json.loads(report.read_bytes()))

    def test_cli_failure_also_keeps_unknown_live_coverage_and_false_gate(self):
        report = self.root / "captured-failure.json"
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(path="../SYNTHETIC_SECRET"))
        code, output, error = self.invoke_cli(report)
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        result = json.loads(report.read_bytes())
        self.assert_historical_scope(result)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_subcode"], "INVENTORY_READ_OR_PIN")
        self.assertNotIn("SYNTHETIC_SECRET", error)


if __name__ == "__main__":
    unittest.main()
