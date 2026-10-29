"""In-memory, synthetic tests for versioned encrypted backup framing."""
import hashlib
import io
import os
import struct
import contextlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import hermes_encrypted_backup as backup


class _Stream(io.BytesIO):
    def close(self):
        pass

    def fileno(self):
        return 1


class _MemoryPath:
    def __init__(self, initial=None):
        self.data = initial
        self.parent = self

    def mkdir(self, **_kwargs):
        pass

    def exists(self):
        return self.data is not None

    def stat(self):
        return SimpleNamespace(st_size=len(self.data.getvalue()))

    def open(self, mode):
        if mode == "xb":
            if self.data is not None:
                raise FileExistsError
            self.data = _Stream()
            return self.data
        if mode == "rb":
            return io.BytesIO(self.data.getvalue())
        raise AssertionError(mode)


def _path(raw):
    return _MemoryPath(_Stream(raw))


class BackupCodecTests(unittest.TestCase):
    def setUp(self):
        self.key = AESGCM.generate_key(bit_length=256)
        self.chunk_patch = patch.object(backup, "CHUNK_SIZE", 8)
        self.fsync_patch = patch.object(backup.os, "fsync")
        self.chunk_patch.start()
        self.fsync_patch.start()
        self.addCleanup(self.chunk_patch.stop)
        self.addCleanup(self.fsync_patch.stop)

    def encode(self, data, version="HEB2"):
        out = _MemoryPath()
        report = backup.encrypt_stream(io.BytesIO(data), out, self.key, format_version=version)
        return out.data.getvalue(), report

    def decode(self, data, key=None):
        return backup.decrypt_bytes(_path(data), self.key if key is None else key)

    def test_v2_roundtrip_empty_and_multiple_chunks(self):
        for original in (b"", b"abc", b"12345678", b"123456789abcdef"):
            raw, report = self.encode(original)
            self.assertEqual(raw[:4], b"HEB2")
            self.assertEqual(self.decode(raw), original)
            self.assertEqual(report["plaintext_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(report["payload_format"], "HEB2")

    def test_v2_default_and_explicit_legacy_requires_trusted_pins(self):
        out = _MemoryPath()
        backup.encrypt_stream(io.BytesIO(b"123456789"), out, self.key)
        raw = out.data.getvalue()
        self.assertEqual(raw[:4], b"HEB2")
        raw, report = self.encode(b"123456789", version="HEB1")
        with self.assertRaisesRegex(ValueError, "trusted"):
            self.decode(raw)
        pins = dict(expected_format="HEB1", expected_ciphertext_sha256=report["ciphertext_sha256"],
                    expected_plaintext_sha256=report["plaintext_sha256"], expected_plaintext_bytes=9)
        self.assertEqual(backup.decrypt_bytes(_path(raw), self.key, **pins), b"123456789")
        end = 12 + 4 + struct.unpack(">I", raw[12:16])[0]
        with self.assertRaisesRegex(ValueError, "identity"):
            backup.decrypt_bytes(_path(raw[:end] + bytes(4)), self.key, **pins)

    def test_every_truncation_and_added_trailing_data_rejected(self):
        raw, _ = self.encode(b"123456789")
        for i in range(len(raw)):
            with self.subTest(cut=i), self.assertRaises((ValueError, InvalidTag)):
                self.decode(raw[:i])
        with self.assertRaises(ValueError):
            self.decode(raw + b"x")

    def test_zero_terminator_at_chunk_boundary_rejected(self):
        raw, _ = self.encode(b"123456789")
        end = 20 + 4 + struct.unpack(">I", raw[20:24])[0]
        with self.assertRaises((ValueError, InvalidTag)):
            self.decode(raw[:end] + bytes(4))

    def test_wrong_key_and_empty_forgery_rejected(self):
        wrong_key = AESGCM.generate_key(bit_length=256)
        for payload in (b"", b"some data"):
            raw, _ = self.encode(payload)
            with self.assertRaises(InvalidTag):
                self.decode(raw, wrong_key)
        with self.assertRaises(ValueError):
            self.decode(b"HEB2" + os.urandom(16) + bytes(4), wrong_key)

    def test_explicit_expected_format_blocks_legacy_downgrade(self):
        legacy, _ = self.encode(b"", version="HEB1")
        with self.assertRaisesRegex(ValueError, "format mismatch"):
            backup.decrypt_bytes(_path(legacy), self.key, expected_format="HEB2")
        v2, _ = self.encode(b"ok")
        self.assertEqual(backup.decrypt_bytes(_path(v2), self.key, expected_format="HEB2"), b"ok")

    def test_v2_rejects_non_256_bit_key(self):
        out = _MemoryPath()
        with self.assertRaises(ValueError):
            backup.encrypt_stream(io.BytesIO(b"a"), out, bytes(16), format_version="HEB2")
        self.assertFalse(out.exists())

    def test_frame_length_bounds(self):
        raw, _ = self.encode(b"123456789")
        for length in (1, 16, 25, 0xFFFFFFFF):
            mutated = raw[:20] + struct.pack(">I", length) + raw[24:]
            with self.subTest(length=length), self.assertRaises(ValueError):
                self.decode(mutated)

    def test_reorder_duplicate_and_remove_frames(self):
        raw, _ = self.encode(b"123456789abcdef")
        end1 = 24 + struct.unpack(">I", raw[20:24])[0]
        end2 = end1 + 4 + struct.unpack(">I", raw[end1:end1 + 4])[0]
        f1, f2, tail = raw[20:end1], raw[end1:end2], raw[end2:]
        for mutated in (raw[:20] + f2 + f1 + tail, raw[:20] + f1 + f1 + tail,
                        raw[:20] + f1 + tail):
            with self.assertRaises((ValueError, InvalidTag)):
                self.decode(mutated)

    def test_ciphertext_and_final_tag_tamper(self):
        raw, _ = self.encode(b"abcdef")
        for index in (24, len(raw) - 1):
            mutated = bytearray(raw)
            mutated[index] ^= 1
            with self.assertRaises(InvalidTag):
                self.decode(bytes(mutated))

    def test_cross_payload_splicing_rejected(self):
        a, _ = self.encode(b"123456789")
        b, _ = self.encode(b"abcdefghz")
        self.assertNotEqual(a[4:20], b[4:20])
        end = 24 + struct.unpack(">I", a[20:24])[0]
        with self.assertRaises(InvalidTag):
            self.decode(a[:end] + b[end:])

    def test_validly_authenticated_wrong_summary_rejected(self):
        raw, _ = self.encode(b"abcdef")
        sentinel = len(raw) - backup._V2_FINAL_CIPHERTEXT_SIZE - 4
        salt = raw[4:20]
        counter = (1).to_bytes(4, "big")
        for summary in (struct.pack(">IQ", 2, 6) + hashlib.sha256(b"abcdef").digest(),
                        struct.pack(">IQ", 1, 7) + hashlib.sha256(b"abcdef").digest(),
                        struct.pack(">IQ", 1, 6) + bytes(32)):
            final = backup._v2_aes(self.key, salt).encrypt(bytes(8) + counter, summary, backup._V2_FINAL_AAD + counter)
            with self.assertRaises(ValueError):
                self.decode(raw[:sentinel + 4] + final)

    def test_invalid_version_does_not_create_output(self):
        out = _MemoryPath()
        with self.assertRaises(ValueError):
            backup.encrypt_stream(io.BytesIO(b"a"), out, self.key, format_version="HEB3")
        self.assertFalse(out.exists())

    def test_v2_plaintext_limit_before_read_and_append(self):
        raw, _ = self.encode(b"123456789")
        reads = []
        class TrackedStream(io.BytesIO):
            def read(self, n=-1):
                reads.append(n)
                return super().read(n)
        class TrackedPath:
            def open(self, mode):
                return TrackedStream(raw)
        with patch.object(backup, "_V2_MAX_PLAINTEXT", 8):
            with self.assertRaises(ValueError):
                backup.decrypt_bytes(TrackedPath(), self.key, expected_format="HEB2")
            self.assertNotIn(17, reads)  # second ciphertext is never requested
            with self.assertRaises(ValueError):
                self.encode(b"123456789")
            bounded, _ = self.encode(b"12345678")
            self.assertEqual(self.decode(bounded), b"12345678")

    def test_v2_cipher_and_frame_limits(self):
        raw, _ = self.encode(b"123456789")
        empty, _ = self.encode(b"")
        for name, limit in (("_V2_MAX_CIPHERTEXT", 111), ("_V2_MAX_FRAMES", 1)):
            with self.subTest(limit=name), patch.object(backup, name, limit):
                with self.assertRaises(ValueError):
                    self.decode(raw)
                with self.assertRaises(ValueError):
                    self.encode(b"123456789")
        with patch.object(backup, "_V2_MAX_CIPHERTEXT", 83):
            with self.assertRaises(ValueError):
                self.decode(empty)
            out = _MemoryPath()
            with self.assertRaises(ValueError):
                backup.encrypt_stream(io.BytesIO(b""), out, self.key, format_version="HEB2")
            self.assertFalse(out.exists())

    def test_legacy_oversized_declared_chunk_rejected_before_read(self):
        reads = []
        class TrackedStream(io.BytesIO):
            def read(self, n=-1):
                reads.append(n)
                return super().read(n)
        class TrackedPath:
            def open(self, mode):
                return TrackedStream(b"HEB1" + bytes(8) + struct.pack(">I", 0xffffffff))
        with self.assertRaises(ValueError):
            backup.decrypt_bytes(TrackedPath(), self.key)
        self.assertNotIn(0xffffffff, reads)

    def test_heb2_commands_forward_format_and_limits(self):
        base = ["backup", "--key-file", "synthetic-key", "--report", "synthetic-report"]
        commands = [
            ["encrypt-command", *base[1:], "--destination", "synthetic", "--cwd", ".", "--payload-format", "HEB2", "--", "example"],
            ["sqlite-backup", *base[1:], "--source", "synthetic", "--destination", "synthetic", "--payload-format", "HEB2"],
        ]
        for command in commands:
            with self.subTest(command=command[0]), patch.object(sys, "argv", ["backup", *command]), \
                 patch.object(backup, "load_key", return_value=self.key), \
                 patch.object(backup.subprocess, "Popen") as popen, \
                 patch.object(backup, "sqlite_backup", return_value={}) as sqlite_backup, \
                 patch.object(backup, "encrypt_command", return_value={}) as encrypt_command, \
                 patch.object(backup, "write_json_exclusive"), \
                 patch.object(backup.Path, "exists", return_value=True), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(backup.main(), 0)
                popen.assert_not_called()
                called = sqlite_backup if command[0] == "sqlite-backup" else encrypt_command
                self.assertEqual(called.call_args.kwargs["format_version"], "HEB2")
                self.assertIn("max_plaintext_bytes", called.call_args.kwargs)

    def test_public_failure_report_does_not_leak_exception(self):
        argv = ["backup", "verify-run", "--key-file", "synthetic-key", "--manifest", "synthetic-manifest", "--run-root", "synthetic-root", "--report", "synthetic-report", "--expected-manifest-sha256", "0" * 64]
        out = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(backup, "load_key", return_value=self.key), \
             patch.object(backup, "verify_run", side_effect=ValueError("SYNTHETIC_CONFIG_SECRET")), \
             patch.object(backup, "write_json_exclusive") as report, \
             patch.object(backup.Path, "exists", return_value=False), \
             contextlib.redirect_stderr(out):
            self.assertEqual(backup.main(), 1)
            self.assertEqual(report.call_args.args[1], {"status": "failed", "error_code": "INVALID_INPUT"})
            self.assertNotIn("SYNTHETIC_CONFIG_SECRET", out.getvalue())


if __name__ == "__main__":
    unittest.main()
