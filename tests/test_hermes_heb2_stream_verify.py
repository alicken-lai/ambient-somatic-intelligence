"""Synthetic, memory-bounded tests of the HEB2 verifier; no backup files."""
import hashlib
import io
import struct
import unittest

from scripts import hermes_encrypted_backup as codec
from scripts.hermes_heb2_stream_verify import verify_heb2_stream


KEY = bytes(range(32))
SALT = bytes(range(16))


class SyntheticStream:
    """Generate ciphertext on demand; never retain the complete fixture."""
    def __init__(self, size, salt=SALT):
        self.size = size
        self.salt = salt
        self.iterator = iter(self._parts())
        self.pending = b""
        self.max_requested = 0

    def _parts(self):
        yield b"HEB2" + self.salt
        aes = codec._v2_aes(KEY, self.salt)
        digest = hashlib.sha256()
        remaining = self.size
        count = 0
        while remaining:
            block = b"P" * min(codec.CHUNK_SIZE, remaining)
            remaining -= len(block)
            digest.update(block)
            counter = count.to_bytes(4, "big")
            length = struct.pack(">I", len(block) + 16)
            yield length
            yield aes.encrypt(bytes(8) + counter, block, codec._V2_DATA_AAD + counter + length)
            count += 1
        counter = count.to_bytes(4, "big")
        yield bytes(4)
        yield aes.encrypt(bytes(8) + counter, struct.pack(">IQ", count, self.size) + digest.digest(),
                          codec._V2_FINAL_AAD + counter)

    def read(self, count):
        self.max_requested = max(self.max_requested, count)
        if not self.pending:
            try:
                self.pending = next(self.iterator)
            except StopIteration:
                return b""
        result = self.pending[:count]
        self.pending = self.pending[count:]
        return result


def pins(size, salt=SALT):
    plaintext_hash = hashlib.sha256()
    remaining = size
    while remaining:
        block = b"P" * min(codec.CHUNK_SIZE, remaining)
        plaintext_hash.update(block)
        remaining -= len(block)
    stream = SyntheticStream(size, salt)
    ciphertext_hash = hashlib.sha256()
    cipher_bytes = 0
    while True:
        part = stream.read(65536)
        if not part:
            break
        cipher_bytes += len(part)
        ciphertext_hash.update(part)
    return {
        "expected_format": "HEB2",
        "expected_ciphertext_sha256": ciphertext_hash.hexdigest(),
        "expected_plaintext_sha256": plaintext_hash.hexdigest(),
        "expected_plaintext_bytes": size,
        "max_ciphertext_bytes": cipher_bytes,
        "max_plaintext_bytes": size,
        "max_frames": (size + codec.CHUNK_SIZE - 1) // codec.CHUNK_SIZE,
    }


def raw_fixture(size, salt=SALT):
    stream = SyntheticStream(size, salt)
    result = bytearray()
    while True:
        part = stream.read(65536)
        if not part:
            return bytes(result)
        result.extend(part)


class StreamingVerifyTests(unittest.TestCase):
    def verify(self, stream, size, **changes):
        kwargs = pins(size)
        kwargs.update(changes)
        return verify_heb2_stream(stream, KEY, **kwargs)

    def test_empty_and_small_stream_short_reads(self):
        for size in (0, 1, 100):
            stream = SyntheticStream(size)
            result = self.verify(stream, size)
            self.assertEqual(result["status"], "verified_against_caller_pins")
            self.assertFalse(result["caller_pins_independently_authenticated"])
            self.assertFalse(result["file_identity_or_toctou_verified"])
            self.assertFalse(result["os_memory_or_deadline_verified"])
            self.assertNotIn("plaintext", result)
            self.assertLessEqual(stream.max_requested, codec.CHUNK_SIZE + 16)

    def test_historical_size_synthetic_stream(self):
        size = 75_776_000
        kwargs = pins(size)
        stream = SyntheticStream(size)
        result = verify_heb2_stream(stream, KEY, **kwargs)
        self.assertEqual(result["status"], "verified_against_caller_pins")
        self.assertNotIn("plaintext_bytes", result)
        self.assertNotIn("ciphertext_bytes", result)
        self.assertLessEqual(stream.max_requested, codec.CHUNK_SIZE + 16)

    def test_wrong_key_and_pins(self):
        data = raw_fixture(128)
        kwargs = pins(128)
        with self.assertRaises(ValueError):
            verify_heb2_stream(io.BytesIO(data), bytes(32), **kwargs)
        for name in ("expected_ciphertext_sha256", "expected_plaintext_sha256"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.verify(io.BytesIO(data), 128, **{name: "0" * 64})
        with self.assertRaises(ValueError):
            self.verify(io.BytesIO(data), 128, expected_plaintext_bytes=127)

    def test_truncation_trailing_and_tamper(self):
        data = raw_fixture(80)
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                self.verify(io.BytesIO(data[:end]), 80)
        for candidate in (data + b"x", data[:24] + bytes([data[24] ^ 1]) + data[25:]):
            with self.assertRaises(ValueError):
                self.verify(io.BytesIO(candidate), 80)

    def test_splice_and_legacy_downgrade_rejected(self):
        left = raw_fixture(80)
        right = raw_fixture(80, salt=bytes(reversed(SALT)))
        for candidate in (left[:40] + right[40:], b"HEB1" + bytes(12)):
            with self.assertRaises(ValueError):
                self.verify(io.BytesIO(candidate), 80)

    def test_authenticated_wrong_final_summary_rejected(self):
        raw = raw_fixture(80)
        counter = (1).to_bytes(4, "big")
        for claimed_count, claimed_size, digest in (
                (2, 80, hashlib.sha256(b"P" * 80).digest()),
                (1, 81, hashlib.sha256(b"P" * 80).digest()),
                (1, 80, bytes(32))):
            summary = struct.pack(">IQ", claimed_count, claimed_size) + digest
            final = codec._v2_aes(KEY, SALT).encrypt(bytes(8) + counter, summary, codec._V2_FINAL_AAD + counter)
            modified = raw[:-codec._V2_FINAL_CIPHERTEXT_SIZE] + final
            with self.subTest(count=claimed_count, size=claimed_size), self.assertRaises(ValueError):
                self.verify(io.BytesIO(modified), 80, expected_ciphertext_sha256=hashlib.sha256(modified).hexdigest())

    def test_limit_validation_and_runtime_rejection(self):
        data = raw_fixture(80)
        for changes in ({"expected_format": "HEB1"}, {"max_frames": True},
                        {"max_frames": 0}, {"max_plaintext_bytes": 79},
                        {"max_ciphertext_bytes": 83}, {"max_ciphertext_bytes": len(data) - 1},
                        {"expected_plaintext_bytes": -1}, {"max_frames": codec._V2_MAX_FRAMES + 1},
                        {"expected_ciphertext_sha256": "not-a-hash"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.verify(io.BytesIO(data), 80, **changes)

    def test_oversized_declared_frame_rejected_before_payload_read(self):
        class ReadProbe(io.BytesIO):
            def __init__(self, raw):
                super().__init__(raw)
                self.requests = []
            def read(self, count=-1):
                self.requests.append(count)
                return super().read(count)
        stream = ReadProbe(b"HEB2" + SALT + struct.pack(">I", 0xffffffff))
        with self.assertRaises(ValueError):
            self.verify(stream, 80)
        self.assertNotIn(0xffffffff, stream.requests)

    def test_non_bytes_or_oversized_read_fails_closed(self):
        class BadStream:
            def __init__(self, value): self.value = value
            def read(self, count): return self.value
        for value in ("x", b"x" * 21, None):
            with self.assertRaises(ValueError):
                self.verify(BadStream(value), 80)

    def test_untrusted_input_types_are_rejected_without_magic_methods(self):
        class Hostile:
            def __ne__(self, other):
                raise AssertionError("format comparison was invoked")
            def __len__(self):
                raise AssertionError("key length was invoked")
        class Unreadable:
            def read(self, count):
                raise AssertionError("source was accessed")
        kwargs = pins(0)
        kwargs["expected_format"] = Hostile()
        with self.assertRaisesRegex(ValueError, "^invalid verification request$"):
            verify_heb2_stream(Unreadable(), KEY, **kwargs)
        kwargs["expected_format"] = "HEB2"
        with self.assertRaisesRegex(ValueError, "^invalid verification request$"):
            verify_heb2_stream(Unreadable(), Hostile(), **kwargs)

    def test_reader_exception_is_redacted_but_interrupt_propagates(self):
        class RaisingStream:
            def __init__(self, exc):
                self.exc = exc
            def read(self, count):
                raise self.exc
        with self.assertRaisesRegex(ValueError, "^HEB2 verification failed$") as caught:
            self.verify(RaisingStream(OSError("SYNTHETIC_SECRET")), 0)
        self.assertNotIn("SYNTHETIC_SECRET", str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)
        with self.assertRaises(KeyboardInterrupt):
            self.verify(RaisingStream(KeyboardInterrupt()), 0)


if __name__ == "__main__":
    unittest.main()
