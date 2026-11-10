"""Synthetic bootstrap regressions; no backup, DPAPI, ACL or Hermes startup."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "hermes_backup_bootstrap.py"
SPEC = importlib.util.spec_from_file_location("backup_bootstrap_test_target", BOOTSTRAP)
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / ".staging"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="asi-synthetic-bootstrap-", dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.crypto = self.root / "cryptography"
        self.crypto.mkdir()
        (self.crypto / "__init__.py").write_text("__version__ = '50.0.1'\n", encoding="utf-8")
        self.yaml = self.root / "yaml"
        self.yaml.mkdir()
        (self.yaml / "__init__.py").write_text(
            "__version__='6.0.3'\ntry:\n from .cyaml import *\n"
            "except ImportError:\n __with_libyaml__=False\n"
            "def safe_load(value):\n return {'synthetic': True}\n", encoding="utf-8")
        (self.yaml / "cyaml.py").write_text("raise RuntimeError('NATIVE_CANARY')\n", encoding="utf-8")
        self.helper = self.root / "synthetic_helper.py"
        self.helper.write_text("import yaml\nassert yaml.safe_load('synthetic: true') == {'synthetic':True}\nprint('SYNTHETIC_HELPER_OK')\n", encoding="utf-8")

    def command(self, arguments=(), *, crypto=None, yaml=None, pins=None, cffi=None):
        crypto = crypto or self.crypto
        yaml = yaml or self.yaml
        values = dict(helper=hashlib.sha256(self.helper.read_bytes()).hexdigest(),
            crypto=bootstrap.snapshot_package("cryptography", crypto, allow_native=True)["digest"],
            yaml=bootstrap.snapshot_package("yaml", yaml, allow_native=False)["digest"])
        values.update(pins or {})
        command = [sys.executable, "-I", "-S", "-B", str(BOOTSTRAP),
            "--helper", str(self.helper), "--helper-sha256", values["helper"],
            "--crypto-package", str(crypto), "--crypto-package-sha256", values["crypto"],
            "--yaml-package", str(yaml), "--yaml-package-sha256", values["yaml"]]
        if cffi is not None:
            command += ["--cffi-extension", str(cffi[0]), "--cffi-extension-sha256", cffi[1]]
        return [*command, "--", *arguments]

    def run_child(self, command):
        return subprocess.run(command, cwd=self.root, capture_output=True, text=True,
                              encoding="utf-8", timeout=20, check=False)

    def test_no_site_or_startup_and_pure_yaml(self):
        marker = self.root / "startup-ran"
        (self.root / "sitecustomize.py").write_text("raise RuntimeError('STARTUP_CANARY')\n")
        (self.root / "unsafe.pth").write_text("import pathlib; pathlib.Path('startup-ran').touch()\n")
        self.helper.write_text(
            "import sys,yaml\nassert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode\n"
            "assert not yaml.__with_libyaml__\nassert 'yaml.cyaml' not in sys.modules\n"
            "assert not any('site-packages' in p for p in sys.path)\nprint('ISOLATED_PURE_YAML_OK')\n")
        result = self.run_child(self.command())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ISOLATED_PURE_YAML_OK", result.stdout)
        self.assertFalse(marker.exists())

    def test_helper_arguments_are_forwarded_without_shell_interpretation(self):
        arguments = ["--report", "a b", "synthetic'$()`", "雙語", "--", "trailing"]
        self.helper.write_text("import sys\nassert sys.argv[1:] == " + repr(arguments)
                               + "\nprint('ARGV_EXACT_OK')\n", encoding="utf-8")
        result = self.run_child(self.command(arguments))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ARGV_EXACT_OK", result.stdout)

    def test_wrong_helper_or_package_pin_refuses_helper(self):
        marker = self.root / "helper-ran"
        self.helper.write_text("from pathlib import Path\nPath('helper-ran').touch()\n")
        for name in ("helper", "crypto", "yaml"):
            with self.subTest(pin=name):
                result = self.run_child(self.command(pins={name: "0" * 64}))
                self.assertEqual(result.returncode, 1)
                self.assertFalse(marker.exists())

    def test_unpinned_module_is_not_loaded_after_snapshot(self):
        package = bootstrap.snapshot_package("yaml", self.yaml, allow_native=False)
        (self.yaml / "unexpected.py").write_text("raise RuntimeError('UNPINNED_CANARY')")
        finder = bootstrap._PackageFinder([package])
        with self.assertRaises(ModuleNotFoundError):
            finder.find_spec("yaml.unexpected")

    def test_snapshot_source_bytes_are_used_after_file_changes(self):
        package = bootstrap.snapshot_package("yaml", self.yaml, allow_native=False)
        (self.yaml / "__init__.py").write_text("raise RuntimeError('CHANGED_CANARY')")
        spec = bootstrap._PackageFinder([package]).find_spec("yaml")
        self.assertNotIn(b"CHANGED_CANARY", spec.loader.raw)
        self.assertIn(b"__version__='6.0.3'", spec.loader.raw)

    def test_modified_package_fails_exact_pin(self):
        command = self.command()
        (self.yaml / "__init__.py").write_text("raise RuntimeError('CHANGED_CANARY')")
        result = self.run_child(command)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("CHANGED_CANARY", result.stderr)

    def test_version_mismatch_and_helper_exception_are_sanitized(self):
        (self.crypto / "__init__.py").write_text("__version__='49.0.0'\n")
        result = self.run_child(self.command())
        self.assertEqual(result.returncode, 1)
        (self.crypto / "__init__.py").write_text("__version__='50.0.1'\n")
        self.helper.write_text("raise ValueError('SYNTHETIC_SECRET_DO_NOT_PRINT')\n")
        result = self.run_child(self.command())
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("SYNTHETIC_SECRET_DO_NOT_PRINT", result.stderr)
        self.assertNotIn(str(self.root), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_helper_exit_code_is_preserved_without_printing_string_errors(self):
        for code, expected in ((0, 0), (3, 3), ("SYNTHETIC_SECRET", 1)):
            with self.subTest(code=code):
                self.helper.write_text("raise SystemExit(" + repr(code) + ")\n")
                result = self.run_child(self.command())
                self.assertEqual(result.returncode, expected)
                self.assertNotIn("SYNTHETIC_SECRET", result.stderr)

    def test_nonisolated_invocation_is_rejected(self):
        # Check rejection without starting another interpreter with site enabled.
        with patch.object(bootstrap.sys, "flags", SimpleNamespace(isolated=0, no_site=1)):
            with self.assertRaisesRegex(ValueError, "isolated"):
                bootstrap.run_pinned(self.helper, "0" * 64, self.crypto,
                    "0" * 64, self.yaml, "0" * 64, [])

    def test_bad_cffi_pin_is_rejected_before_helper(self):
        native = self.root / "_cffi_backend.pyd"
        native.write_bytes(b"synthetic non-executable fixture")
        result = self.run_child(self.command(cffi=(native, "0" * 64)))
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("SYNTHETIC_HELPER_OK", result.stdout)

    def test_package_limits_and_missing_initializer(self):
        initializer = self.yaml / "__init__.py"
        initializer.unlink()
        with self.assertRaisesRegex(ValueError, "initializer"):
            bootstrap.snapshot_package("yaml", self.yaml, allow_native=False)
        initializer.write_text("x=1")
        old_limit = bootstrap._MAX_PACKAGE_FILES
        try:
            bootstrap._MAX_PACKAGE_FILES = 1
            with self.assertRaisesRegex(ValueError, "limit"):
                bootstrap.snapshot_package("yaml", self.yaml, allow_native=False)
        finally:
            bootstrap._MAX_PACKAGE_FILES = old_limit

    @unittest.skipUnless(os.environ.get("ASI_BACKUP_BOOTSTRAP_YAML_PACKAGE")
                         and os.environ.get("ASI_BACKUP_BOOTSTRAP_YAML_SHA256")
                         and os.environ.get("ASI_BACKUP_BOOTSTRAP_CRYPTO_SHA256")
                         and os.environ.get("ASI_BACKUP_BOOTSTRAP_CFFI_EXTENSION")
                         and os.environ.get("ASI_BACKUP_BOOTSTRAP_CFFI_SHA256"),
                         "explicit existing dependency pins required")
    def test_real_bundled_crypto_and_exact_yaml_safe_load(self):
        crypto = Path(sys.executable).parent / "Lib" / "site-packages" / "cryptography"
        yaml = Path(os.environ["ASI_BACKUP_BOOTSTRAP_YAML_PACKAGE"])
        self.helper.write_text(
            "import sys,yaml,cryptography\nfrom cryptography.hazmat.primitives.ciphers.aead import AESGCM\n"
            "from cryptography.hazmat.primitives.kdf.hkdf import HKDF\n"
            "from cryptography.hazmat.primitives import hashes\n"
            "assert yaml.safe_load('synthetic: true') == {'synthetic':True}\n"
            "assert yaml.__with_libyaml__ is False\n"
            "key=HKDF(algorithm=hashes.SHA256(),length=32,salt=b'synthetic',info=b'smoke').derive(bytes(32))\n"
            "aes=AESGCM(key); nonce=bytes(12); ciphertext=aes.encrypt(nonce,b'synthetic',b'aad')\n"
            "assert aes.decrypt(nonce,ciphertext,b'aad')==b'synthetic'\n"
            "assert not any('site-packages' in p for p in sys.path)\nprint('REAL_PINNED_DEPENDENCY_SMOKE_OK')\n")
        result = self.run_child(self.command(crypto=crypto, yaml=yaml, pins={
            "crypto": os.environ["ASI_BACKUP_BOOTSTRAP_CRYPTO_SHA256"],
            "yaml": os.environ["ASI_BACKUP_BOOTSTRAP_YAML_SHA256"]}, cffi=(
            Path(os.environ["ASI_BACKUP_BOOTSTRAP_CFFI_EXTENSION"]),
            os.environ["ASI_BACKUP_BOOTSTRAP_CFFI_SHA256"])))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("REAL_PINNED_DEPENDENCY_SMOKE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
