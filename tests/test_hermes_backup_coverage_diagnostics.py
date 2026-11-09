"""Coverage failure identifiers using only new synthetic fixtures.

Existing codec/integration tests are reused without editing their sources.
No production DB, DPAPI, Windows ACL command or historical run is accessed.
"""
import contextlib
import io
import json
import os
import sys
import unittest
from unittest.mock import patch

from scripts import hermes_encrypted_backup as backup
from tests import test_hermes_encrypted_backup_integration as fixtures

KEY = fixtures.KEY


class CoverageDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BackupIntegrationTests(methodName="test_trusted_manifest_and_full_synthetic_run")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.manifest, self.expected = self.fixture.manifest_fixture()

    def rewrite_manifest(self, mutate):
        value = json.loads(self.manifest.read_bytes())
        mutate(value)
        self.manifest.write_text(json.dumps(value), encoding="utf-8")
        self.expected = backup.sha256_file(self.manifest)

    def rewrite_inventory(self, mutate):
        value = json.loads(self.manifest.read_bytes())
        inventory_path = self.root / value["home_source_inventory"]["path"]
        inventory = json.loads(inventory_path.read_bytes())
        mutate(inventory)
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(
            sha256=backup.sha256_file(inventory_path)))

    def invoke_failure(self, stage, subcode, primary="INVALID_INPUT"):
        report = self.root / "synthetic-failure-report.json"
        argv = ["synthetic-backup", "verify-run", "--key-file", "synthetic-key",
            "--manifest", str(self.manifest), "--run-root", str(self.root),
            "--report", str(report), "--expected-manifest-sha256", self.expected]
        stderr = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(backup, "load_key", return_value=KEY), \
             patch.object(backup, "_make_private_restore_root") as make_root, \
             contextlib.redirect_stderr(stderr):
            self.assertEqual(backup.main(), 1)
            make_root.assert_not_called()
        observed = json.loads(report.read_bytes())
        self.assertEqual(observed, {"status": "failed", "error_code": primary,
            "error_stage": stage, "error_subcode": subcode})
        self.assertIn("stage=" + stage, stderr.getvalue())
        self.assertIn("subcode=" + subcode, stderr.getvalue())
        self.assertNotIn("SYNTHETIC_SECRET", stderr.getvalue())
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(observed))
        self.assertNotIn(str(self.root), stderr.getvalue())
        return observed

    def test_missing_manifest_target_preserves_keyerror_and_primary_code(self):
        self.rewrite_manifest(lambda data: data.pop("exact_targets"))
        with self.assertRaises(KeyError) as caught:
            backup.verify_run(self.root, self.manifest, KEY, expected_manifest_sha256=self.expected)
        self.assertEqual(backup._public_coverage_failure(caught.exception),
            {"error_stage": "COVERAGE_MANIFEST", "error_subcode": "TARGET_FIELDS"})
        self.invoke_failure("COVERAGE_MANIFEST", "TARGET_FIELDS", "OPERATION_FAILED")

    def test_bad_inventory_reference_is_not_live_drift(self):
        self.rewrite_manifest(lambda data: data.update(home_source_inventory="SYNTHETIC_SECRET"))
        self.invoke_failure("COVERAGE_MANIFEST", "INVENTORY_REFERENCE")

    def test_missing_inventory_keeps_requirement(self):
        self.rewrite_manifest(lambda data: data.pop("home_source_inventory"))
        self.invoke_failure("COVERAGE_CAPTURED", "INVENTORY_REQUIRED")

    def test_missing_sidecar_preserves_file_not_found_without_path_disclosure(self):
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(
            path="SYNTHETIC_SECRET_missing_inventory.json"))
        self.invoke_failure("COVERAGE_CAPTURED", "INVENTORY_READ_OR_PIN", "FILE_NOT_FOUND")

    def test_wrong_inventory_pin_is_distinct_from_shape(self):
        self.rewrite_manifest(lambda data: data["home_source_inventory"].update(sha256="0" * 64))
        self.invoke_failure("COVERAGE_CAPTURED", "INVENTORY_READ_OR_PIN")

    def test_bad_inventory_schema_is_fixed_shape_failure(self):
        self.rewrite_inventory(lambda data: data.update(schema="SYNTHETIC_SECRET"))
        self.invoke_failure("COVERAGE_CAPTURED", "INVENTORY_SHAPE")

    def test_invalid_entry_is_fixed_entry_failure(self):
        self.rewrite_inventory(lambda data: data["entries"].append("SYNTHETIC_SECRET"))
        self.invoke_failure("COVERAGE_CAPTURED", "INVENTORY_ENTRY")

    def test_invalid_acl_is_not_live_drift(self):
        self.rewrite_inventory(lambda data: data.update(source_acl_sddl="SYNTHETIC_SECRET"))
        self.invoke_failure("COVERAGE_CAPTURED", "INVENTORY_ACL")

    def test_missing_payload_is_still_rejected(self):
        self.rewrite_manifest(lambda data: data.update(items=[item for item in data["items"]
            if not (item["category"] == "hermes-home-file" and item["relative_path"] == ".env")]))
        self.invoke_failure("COVERAGE_CAPTURED", "PAYLOAD_MAPPING")

    def test_live_added_file_still_refuses_success(self):
        (self.root / "synthetic-home/SYNTHETIC_SECRET_added.txt").write_bytes(b"synthetic")
        self.invoke_failure("COVERAGE_LIVE", "LIVE_INVENTORY_CHANGED")

    def test_live_same_size_mtime_change_still_refuses_success(self):
        source = self.root / "synthetic-home/config.yaml"
        before = source.stat()
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        self.invoke_failure("COVERAGE_LIVE", "LIVE_INVENTORY_CHANGED")

    def test_live_read_error_preserves_permissionerror_and_redacts_message(self):
        with patch.object(backup, "inventory_home", side_effect=PermissionError("SYNTHETIC_SECRET")):
            with self.assertRaises(PermissionError):
                backup.verify_run(self.root, self.manifest, KEY, expected_manifest_sha256=self.expected)
            self.invoke_failure("COVERAGE_LIVE", "LIVE_INVENTORY_READ", "OPERATION_FAILED")

    def test_unclassified_failure_does_not_publish_dynamic_text(self):
        payload = json.loads(self.manifest.read_bytes())
        payload["items"] = ["SYNTHETIC_SECRET"]
        with self.assertRaises(AttributeError) as caught:
            backup._verify_home_coverage(self.root, payload, payload["items"], legacy=False)
        self.assertEqual(backup._public_coverage_failure(caught.exception),
            {"error_stage": "COVERAGE_PRECHECK", "error_subcode": "UNCLASSIFIED"})

    def test_unallowlisted_error_attribute_is_never_published(self):
        error = ValueError("SYNTHETIC_SECRET")
        error._hermes_coverage_subcode = "SYNTHETIC_SECRET"
        self.assertEqual(backup._public_coverage_failure(error), {})

    def test_unchanged_success_and_legacy_absence_behavior_are_preserved(self):
        payload = json.loads(self.manifest.read_bytes())
        result = backup._verify_home_coverage(self.root, payload, payload["items"], legacy=False)
        self.assertTrue(result["complete"])
        self.assertTrue(result["source_remeasured"])
        del payload["home_source_inventory"]
        legacy = backup._verify_home_coverage(self.root, payload, payload["items"], legacy=True)
        self.assertEqual(legacy["state"], "LEGACY_COVERAGE_UNKNOWN")
        self.assertFalse(legacy["complete"])


if __name__ == "__main__":
    unittest.main()
