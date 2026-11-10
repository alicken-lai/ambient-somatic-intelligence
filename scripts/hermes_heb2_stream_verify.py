"""Candidate HEB2 streaming verifier; not an operational restore adapter.

Inputs are caller-supplied pins and budgets, NOT evidence that those pins are
authentic. The caller must independently bind them to a trusted operation,
key identity, and payload identity. No plaintext is returned or persisted.
No OS memory limit, hard deadline, immutable-handle, ACL or TOCTOU guarantee is
provided here. Legacy HEB1 is never accepted by this entry point.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import struct

from .hermes_encrypted_backup import (
    CHUNK_SIZE,
    MAGIC_V2,
    _V2_DATA_AAD,
    _V2_FINAL_AAD,
    _V2_FINAL_CIPHERTEXT_SIZE,
    _V2_MAX_FRAMES,
    _v2_aes,
)


def verify_heb2_stream(
    source,
    key: bytes,
    *,
    expected_format: str,
    expected_ciphertext_sha256: str,
    expected_plaintext_sha256: str,
    expected_plaintext_bytes: int,
    max_ciphertext_bytes: int,
    max_plaintext_bytes: int,
    max_frames: int,
) -> dict[str, object]:
    """Verify one HEB2 stream under explicit caller-supplied limits and pins.

    The input must expose a blocking read(n) returning at most n built-in
    bytes; short reads are supported. Caller-provided pins are not authenticated
    by this function. File identity, concurrent mutation and authority belong
    to a separately reviewed caller. Only the completed summary is returned.
    """
    if type(expected_format) is not str or expected_format != "HEB2":
        raise ValueError("invalid verification request")
    if type(key) is not bytes or len(key) != 32:
        raise ValueError("invalid verification request")
    for value in (expected_ciphertext_sha256, expected_plaintext_sha256):
        if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError("invalid verification request")
    for value in (expected_plaintext_bytes, max_ciphertext_bytes, max_plaintext_bytes, max_frames):
        if type(value) is not int or value < 0 or value > (1 << 63) - 1:
            raise ValueError("invalid verification request")
    if (expected_plaintext_bytes > max_plaintext_bytes or max_ciphertext_bytes < 84
            or max_frames > _V2_MAX_FRAMES):
        raise ValueError("invalid verification request")

    ciphertext_hash = hashlib.sha256()
    plaintext_hash = hashlib.sha256()
    cipher_bytes = 0
    plain_bytes = 0
    chunks = 0

    def read_exact(count: int) -> bytes:
        nonlocal cipher_bytes
        if count > max_ciphertext_bytes - cipher_bytes:
            raise ValueError("HEB2 verification failed")
        parts = bytearray()
        while len(parts) < count:
            part = source.read(count - len(parts))
            if type(part) is not bytes or not part or len(part) > count - len(parts):
                raise ValueError("HEB2 verification failed")
            parts.extend(part)
        result = bytes(parts)
        cipher_bytes += count
        ciphertext_hash.update(result)
        return result

    try:
        header = read_exact(20)
        if header[:4] != MAGIC_V2:
            raise ValueError("HEB2 verification failed")
        aes = _v2_aes(key, header[4:])
        while True:
            length_bytes = read_exact(4)
            length = struct.unpack(">I", length_bytes)[0]
            counter = chunks.to_bytes(4, "big")
            if length == 0:
                final = read_exact(_V2_FINAL_CIPHERTEXT_SIZE)
                summary = aes.decrypt(bytes(8) + counter, final, _V2_FINAL_AAD + counter)
                final_chunks, final_bytes = struct.unpack(">IQ", summary[:12])
                if (final_chunks != chunks or final_bytes != plain_bytes
                        or not hmac.compare_digest(summary[12:], plaintext_hash.digest())):
                    raise ValueError("HEB2 verification failed")
                break
            if (length < 17 or length > CHUNK_SIZE + 16 or chunks >= max_frames
                    or plain_bytes + length - 16 > max_plaintext_bytes
                    or plain_bytes + length - 16 > expected_plaintext_bytes):
                raise ValueError("HEB2 verification failed")
            cipher = read_exact(length)
            block = aes.decrypt(bytes(8) + counter, cipher, _V2_DATA_AAD + counter + length_bytes)
            plaintext_hash.update(block)
            plain_bytes += len(block)
            chunks += 1
            del block, cipher

        # One-byte EOF probe is permitted even if the ciphertext budget is
        # exactly exhausted. A byte returned here is never retained or output.
        tail = source.read(1)
        if type(tail) is not bytes or tail:
            raise ValueError("HEB2 verification failed")
        if (plain_bytes != expected_plaintext_bytes
                or not hmac.compare_digest(plaintext_hash.hexdigest(), expected_plaintext_sha256)
                or not hmac.compare_digest(ciphertext_hash.hexdigest(), expected_ciphertext_sha256)):
            raise ValueError("HEB2 verification failed")
    except Exception:
        raise ValueError("HEB2 verification failed") from None
    return {
        "status": "verified_against_caller_pins",
        "format": "HEB2",
        "caller_pins_independently_authenticated": False,
        "file_identity_or_toctou_verified": False,
        "os_memory_or_deadline_verified": False,
    }
