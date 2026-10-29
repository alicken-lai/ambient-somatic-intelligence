#!/usr/bin/env python3
"""Small fail-closed encrypted-backup primitives for the Hermes upgrade.

Payloads use independently authenticated AES-256-GCM chunks.  The random
master key is stored only as a Windows DPAPI CurrentUser blob.  SQLite online
backups are serialized from memory and encrypted without a plaintext backup
file being written to disk.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
from ctypes import wintypes
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import queue
import re
import shutil
import sqlite3
import stat
import struct
import subprocess
import sys
import threading
import time
import zipfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


MAGIC = b"HEB1"
MAGIC_V2 = b"HEB2"
CHUNK_SIZE = 1024 * 1024
_V2_DATA_AAD = b"HEB2:data:"
_V2_FINAL_AAD = b"HEB2:final:"
_V2_FINAL_PLAINTEXT_SIZE = 44  # uint32 chunks, uint64 bytes, SHA-256
_V2_FINAL_CIPHERTEXT_SIZE = _V2_FINAL_PLAINTEXT_SIZE + 16
_MAX_CHUNKS = (1 << 32) - 1  # reserve the next counter for final authentication
# The operation budget covers four full image equivalents plus fixed headroom.
# It is a conservative admission estimate, not an OS-enforced RSS guarantee.
DEFAULT_MEMORY_BUDGET_BYTES = 512 * 1024 * 1024
_MEMORY_HEADROOM = 16 * 1024 * 1024
_IMAGE_EQUIVALENTS = 4
_V2_MAX_PLAINTEXT = (DEFAULT_MEMORY_BUDGET_BYTES - _MEMORY_HEADROOM) // _IMAGE_EQUIVALENTS
_V2_MAX_FRAMES = 65536
_V2_MAX_CIPHERTEXT = _V2_MAX_PLAINTEXT + 20 * _V2_MAX_FRAMES + 84
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _operation_limit(max_plaintext_bytes: int | None) -> tuple[int, int]:
    if max_plaintext_bytes is None:
        return _V2_MAX_PLAINTEXT, _V2_MAX_CIPHERTEXT
    if type(max_plaintext_bytes) is not int or not 0 < max_plaintext_bytes <= 4 * 1024**3:
        raise ValueError("invalid operation limit")
    return max_plaintext_bytes, max_plaintext_bytes + 20 * _V2_MAX_FRAMES + 84


def _memory_admission(image_bytes: int, memory_budget_bytes: int) -> int:
    if (type(memory_budget_bytes) is not int or memory_budget_bytes <= _MEMORY_HEADROOM
            or memory_budget_bytes > 32 * 1024**3):
        raise ValueError("invalid memory budget")
    estimated = image_bytes * _IMAGE_EQUIVALENTS + _MEMORY_HEADROOM
    if estimated > memory_budget_bytes:
        raise ValueError("operation memory budget exceeded")
    return estimated


def _valid_hash(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _v2_aes(key: bytes, salt: bytes) -> AESGCM:
    if len(key) != 32 or len(salt) != 16:
        raise ValueError("HEB2 requires a 32-byte key and a 16-byte salt")
    derived = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                   info=b"Hermes encrypted backup HEB2 key").derive(key)
    return AESGCM(derived)


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[DATA_BLOB, object]:
    buffer = ctypes.create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _dpapi(data: bytes, protect: bool) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Windows DPAPI is required")
    source, keepalive = _blob(data)
    destination = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    function = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    description = "Hermes upgrade backup key" if protect else None
    if protect:
        ok = function(ctypes.byref(source), description, None, None, None, 0, ctypes.byref(destination))
    else:
        ok = function(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination))
    _ = keepalive
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)


def _exclusive_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def init_key(path: Path) -> None:
    if path.exists():
        raise FileExistsError("key target already exists")
    _exclusive_write(path, _dpapi(os.urandom(32), True))


def load_key(path: Path) -> bytes:
    key = _dpapi(path.read_bytes(), False)
    if len(key) != 32:
        raise ValueError("invalid master key length")
    return key


def encrypt_stream(source, destination: Path, key: bytes, *, format_version: str = "HEB2",
                   max_plaintext_bytes: int | None = None) -> dict[str, object]:
    """Write a new HEB2 payload; HEB1 writing requires an explicit legacy choice.

    HEB2 authenticates the terminal record and whole-stream summary.
    HEB1 authenticates individual chunks only, not stream completeness, and
    uses the same explicit plaintext/frame budgets as HEB2. Admission limits
    are not an OS memory certification or current database measurement.
    """
    if format_version not in {"HEB1", "HEB2"}:
        raise ValueError("unsupported encrypted payload format")
    plain_limit, cipher_limit = _operation_limit(max_plaintext_bytes)
    if destination.exists():
        raise FileExistsError("encrypted target already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if format_version == "HEB2":
        salt = os.urandom(16)
        aes = _v2_aes(key, salt)
        nonce_prefix = bytes(8)
        header = MAGIC_V2 + salt
    else:
        aes = AESGCM(key)
        nonce_prefix = os.urandom(8)
        header = MAGIC + nonce_prefix
    plain_hash = hashlib.sha256()
    plain_bytes = 0
    chunks = 0
    cipher_bytes = len(header) + 4 + _V2_FINAL_CIPHERTEXT_SIZE if format_version == "HEB2" else 0
    if format_version == "HEB2" and cipher_bytes > cipher_limit:
        raise ValueError("encrypted payload limits exceeded")
    with destination.open("xb") as output:
        output.write(header)
        while True:
            read_size = min(CHUNK_SIZE, plain_limit - plain_bytes + 1)
            block = source.read(read_size)
            if type(block) is not bytes or len(block) > read_size:
                raise ValueError("invalid source stream")
            if not block:
                break
            if plain_bytes + len(block) > plain_limit or chunks >= _V2_MAX_FRAMES:
                raise ValueError("encrypted payload limits exceeded")
            if format_version == "HEB2":
                next_cipher_bytes = cipher_bytes + 4 + len(block) + 16
                if (chunks >= min(_MAX_CHUNKS, _V2_MAX_FRAMES) or len(block) > read_size
                        or len(block) > CHUNK_SIZE or plain_bytes + len(block) > plain_limit
                        or next_cipher_bytes > cipher_limit):
                    raise ValueError("encrypted payload limits exceeded")
                cipher_bytes = next_cipher_bytes
            counter = chunks.to_bytes(4, "big")
            nonce = nonce_prefix + counter
            length_bytes = struct.pack(">I", len(block) + 16)
            aad = (_V2_DATA_AAD + counter + length_bytes) if format_version == "HEB2" else MAGIC + counter
            cipher = aes.encrypt(nonce, block, aad)
            output.write(struct.pack(">I", len(cipher)))
            output.write(cipher)
            plain_hash.update(block)
            plain_bytes += len(block)
            chunks += 1
        output.write(struct.pack(">I", 0))
        if format_version == "HEB2":
            counter = chunks.to_bytes(4, "big")
            summary = struct.pack(">IQ", chunks, plain_bytes) + plain_hash.digest()
            output.write(aes.encrypt(nonce_prefix + counter, summary, _V2_FINAL_AAD + counter))
        output.flush()
        os.fsync(output.fileno())
    return {
        "plaintext_bytes": plain_bytes,
        "plaintext_sha256": plain_hash.hexdigest(),
        "ciphertext_bytes": destination.stat().st_size,
        "ciphertext_sha256": sha256_file(destination),
        "chunks": chunks,
        "payload_format": format_version,
    }


def _decrypt_bytes_with_format(path: Path, key: bytes, *, expected_format: str | None = None,
                               expected_ciphertext_sha256: str | None = None,
                               expected_plaintext_sha256: str | None = None,
                               expected_plaintext_bytes: int | None = None,
                               max_plaintext_bytes: int | None = None) -> tuple[bytes, str]:
    if expected_format not in {None, "HEB1", "HEB2"}:
        raise ValueError("unsupported expected payload format")
    plain_limit, cipher_limit = _operation_limit(max_plaintext_bytes)
    if expected_plaintext_bytes is not None and (type(expected_plaintext_bytes) is not int
            or not 0 <= expected_plaintext_bytes <= plain_limit):
        raise ValueError("invalid expected plaintext size")
    for pin in (expected_ciphertext_sha256, expected_plaintext_sha256):
        if pin is not None and not _valid_hash(pin):
            raise ValueError("invalid expected payload hash")
    restored = bytearray()
    ciphertext_hash = hashlib.sha256()
    with path.open("rb") as raw_source:
        class HashedReader:
            def read(self, count):
                value = raw_source.read(count)
                if type(value) is not bytes or len(value) > count:
                    raise ValueError("invalid encrypted stream")
                ciphertext_hash.update(value)
                return value
        source = HashedReader()
        magic = source.read(4)
        if magic not in {MAGIC, MAGIC_V2}:
            raise ValueError("invalid encrypted payload header")
        if expected_format is not None and magic.decode("ascii") != expected_format:
            raise ValueError("encrypted payload format mismatch")
        is_v2 = magic == MAGIC_V2
        if not is_v2 and (expected_format != "HEB1"
                or expected_ciphertext_sha256 is None or expected_plaintext_sha256 is None
                or expected_plaintext_bytes is None):
            raise ValueError("legacy HEB1 requires explicit independently trusted whole-payload pins")
        header_value = source.read(16 if is_v2 else 8)
        if len(header_value) != (16 if is_v2 else 8):
            raise ValueError("truncated encrypted payload header")
        aes = _v2_aes(key, header_value) if is_v2 else AESGCM(key)
        prefix = bytes(8) if is_v2 else header_value
        counter_value = 0
        plain_hash = hashlib.sha256()
        cipher_bytes = 20 + 4 + _V2_FINAL_CIPHERTEXT_SIZE if is_v2 else 0
        if is_v2 and cipher_bytes > cipher_limit:
            raise ValueError("encrypted payload limits exceeded")
        while True:
            raw_length = source.read(4)
            if len(raw_length) != 4:
                raise ValueError("truncated encrypted payload")
            length = struct.unpack(">I", raw_length)[0]
            if length == 0:
                if is_v2:
                    final = source.read(_V2_FINAL_CIPHERTEXT_SIZE)
                    if len(final) != _V2_FINAL_CIPHERTEXT_SIZE:
                        raise ValueError("truncated encrypted final frame")
                    counter = counter_value.to_bytes(4, "big")
                    summary = aes.decrypt(prefix + counter, final, _V2_FINAL_AAD + counter)
                    chunks, plain_bytes = struct.unpack(">IQ", summary[:12])
                    if (chunks != counter_value or plain_bytes != len(restored)
                            or not hmac.compare_digest(summary[12:], plain_hash.digest())):
                        raise ValueError("encrypted final summary mismatch")
                if source.read(1):
                    raise ValueError("trailing encrypted payload data")
                break
            if length < 17 or length > CHUNK_SIZE + 16:
                raise ValueError("invalid encrypted chunk length or count")
            if (counter_value >= _V2_MAX_FRAMES or len(restored) + length - 16 > plain_limit
                    or (expected_plaintext_bytes is not None
                        and len(restored) + length - 16 > expected_plaintext_bytes)):
                raise ValueError("encrypted payload limits exceeded")
            if is_v2:
                next_cipher_bytes = cipher_bytes + 4 + length
                if (counter_value >= min(_MAX_CHUNKS, _V2_MAX_FRAMES)
                        or len(restored) + length - 16 > plain_limit
                        or next_cipher_bytes > cipher_limit):
                    raise ValueError("encrypted payload limits exceeded")
                cipher_bytes = next_cipher_bytes
            cipher = source.read(length)
            if len(cipher) != length:
                raise ValueError("truncated encrypted chunk")
            counter = counter_value.to_bytes(4, "big")
            aad = (_V2_DATA_AAD + counter + raw_length) if is_v2 else MAGIC + counter
            block = aes.decrypt(prefix + counter, cipher, aad)
            restored.extend(block)
            plain_hash.update(block)
            counter_value += 1
    if (expected_plaintext_bytes is not None and len(restored) != expected_plaintext_bytes
            or expected_plaintext_sha256 is not None
            and not hmac.compare_digest(plain_hash.hexdigest(), expected_plaintext_sha256)
            or expected_ciphertext_sha256 is not None
            and not hmac.compare_digest(ciphertext_hash.hexdigest(), expected_ciphertext_sha256)):
        raise ValueError("whole-payload identity mismatch")
    return bytes(restored), "HEB2" if is_v2 else "HEB1"


def decrypt_bytes(path: Path, key: bytes, *, expected_format: str | None = None,
                  expected_ciphertext_sha256: str | None = None,
                  expected_plaintext_sha256: str | None = None,
                  expected_plaintext_bytes: int | None = None,
                  max_plaintext_bytes: int | None = None) -> bytes:
    """Read HEB2 after full authentication; HEB1 has no authenticated end marker.

    Callers reading HEB1 need an independently trusted whole-payload hash;
    HEB1 has no authenticated end marker and requires all three explicit pins.
    Callers expecting HEB2 must bind expected_format="HEB2" to prevent downgrade.
    """
    return _decrypt_bytes_with_format(path, key, expected_format=expected_format,
        expected_ciphertext_sha256=expected_ciphertext_sha256,
        expected_plaintext_sha256=expected_plaintext_sha256,
        expected_plaintext_bytes=expected_plaintext_bytes,
        max_plaintext_bytes=max_plaintext_bytes)[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_fingerprint(connection: sqlite3.Connection) -> tuple[dict[str, int], str]:
    rows = list(connection.execute(
        "SELECT type, name, tbl_name, COALESCE(sql, '') FROM sqlite_schema "
        "ORDER BY type, name, tbl_name, sql"
    ))
    counts: dict[str, int] = {}
    canonical: list[list[str]] = []
    for object_type, name, table_name, sql in rows:
        kind = str(object_type)
        counts[kind] = counts.get(kind, 0) + 1
        canonical.append([kind, str(name), str(table_name), str(sql)])
    encoded = json.dumps(canonical, ensure_ascii=True, separators=(",", ":")).encode()
    return counts, hashlib.sha256(encoded).hexdigest()


def inspect_db(connection: sqlite3.Connection) -> dict[str, object]:
    connection.execute("PRAGMA temp_store=MEMORY")
    integrity = [str(row[0]) for row in connection.execute("PRAGMA integrity_check")]
    if integrity != ["ok"]:
        raise RuntimeError("SQLite integrity check failed")
    counts, schema_hash = schema_fingerprint(connection)
    return {
        "integrity": integrity,
        "user_version": int(connection.execute("PRAGMA user_version").fetchone()[0]),
        "schema_object_counts": counts,
        "schema_sha256": schema_hash,
    }


def sqlite_backup(source: Path, destination: Path, key: bytes, *, format_version: str = "HEB2",
                  max_plaintext_bytes: int | None = None,
                  memory_budget_bytes: int = DEFAULT_MEMORY_BUDGET_BYTES,
                  timeout_seconds: float = 120.0) -> dict[str, object]:
    plain_limit, _ = _operation_limit(max_plaintext_bytes)
    _memory_admission(plain_limit, memory_budget_bytes)
    if (type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 3600):
        raise ValueError("invalid operation deadline")
    deadline = time.monotonic() + timeout_seconds

    def guard():
        if time.monotonic() >= deadline:
            raise TimeoutError("SQLite backup deadline exceeded")

    source = source.resolve(strict=True)
    uri = source.as_uri() + "?mode=ro"
    original = sqlite3.connect(uri, uri=True, timeout=min(30, timeout_seconds))
    try:
        original.execute("PRAGMA query_only=ON")
        original.execute("PRAGMA trusted_schema=OFF")
        original.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        page_size = int(original.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(original.execute("PRAGMA page_count").fetchone()[0])
        required_bytes = page_size * page_count
        if required_bytes > plain_limit:
            raise ValueError("SQLite image exceeds operation limit")
        estimated_memory = _memory_admission(required_bytes, memory_budget_bytes)
        source_report = inspect_db(original)
        memory = sqlite3.connect(":memory:")
        try:
            def progress(_status, _remaining, total):
                guard()
                if total * page_size > plain_limit:
                    raise ValueError("SQLite image grew beyond operation limit")
                _memory_admission(total * page_size, memory_budget_bytes)
            original.backup(memory, pages=256, progress=progress, sleep=0.05)
            memory.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            backup_report = inspect_db(memory)
            if backup_report != source_report:
                raise RuntimeError("SQLite online backup metadata mismatch")
            serialized = memory.serialize()
            if len(serialized) > plain_limit:
                raise ValueError("SQLite image exceeds operation limit")
            estimated_memory = _memory_admission(len(serialized), memory_budget_bytes)
        finally:
            memory.close()
    finally:
        original.close()
    guard()
    with io.BytesIO(serialized) as stream:
        encrypted = encrypt_stream(stream, destination, key, format_version=format_version,
                                   max_plaintext_bytes=plain_limit)
    del serialized
    guard()
    restored_bytes = decrypt_bytes(destination, key, expected_format=format_version,
        expected_ciphertext_sha256=encrypted["ciphertext_sha256"],
        expected_plaintext_sha256=encrypted["plaintext_sha256"],
        expected_plaintext_bytes=encrypted["plaintext_bytes"], max_plaintext_bytes=plain_limit)
    guard()
    restore_image = restored_bytes
    header_normalized = False
    if len(restore_image) >= 20 and (restore_image[18] == 2 or restore_image[19] == 2):
        # sqlite3.Connection.serialize() preserves WAL read/write version bytes.
        # An isolated in-memory deserialize has no WAL sidecar, so normalize a
        # verification-only copy to rollback-journal header values.  Page data
        # and the encrypted backup itself remain byte-for-byte unchanged.
        restore_image = bytearray(restored_bytes)
        del restored_bytes
        restore_image[18:20] = b"\x01\x01"
        header_normalized = True
    restored = sqlite3.connect(":memory:")
    try:
        restored.deserialize(restore_image)
        del restore_image
        restored.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        restore_report = inspect_db(restored)
    finally:
        restored.close()
    if restore_report != source_report:
        raise RuntimeError("SQLite encrypted restore smoke mismatch")
    return {
        **encrypted,
        **source_report,
        "online_backup": "ok",
        "encrypted_restore_smoke": "ok",
        "restore_header_normalized_from_wal": header_normalized,
        "operation_plaintext_limit_bytes": plain_limit,
        "memory_budget_bytes": memory_budget_bytes,
        "estimated_memory_bytes": estimated_memory,
        "memory_budget_model": "4 image equivalents plus 16 MiB; not an OS RSS limit",
    }


def write_json_exclusive(path: Path, value: object) -> None:
    _exclusive_write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def encrypt_command(argv: list[str], cwd: Path, destination: Path, key: bytes, *,
                    format_version: str = "HEB2", max_plaintext_bytes: int | None = None,
                    timeout_seconds: float = 120.0,
                    max_stderr_bytes: int = 1024 * 1024) -> dict[str, object]:
    """Encrypt stdout with concurrent bounded, hash-only stderr draining.

    Only this direct child can be terminated, once. A pending reader suppresses
    success. Readers never write ciphertext/reports; queues have finite size.
    Detached descendants and OS hard resource limits are outside this adapter.
    """
    if (type(argv) is not list or not argv or any(type(arg) is not str for arg in argv)
            or type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 3600
            or type(max_stderr_bytes) is not int or not 0 <= max_stderr_bytes <= 64 * 1024**2):
        raise ValueError("invalid command operation")
    _operation_limit(max_plaintext_bytes)
    if format_version not in {"HEB1", "HEB2"} or type(key) is not bytes or len(key) != 32:
        raise ValueError("invalid command encryption request")
    if destination.exists():
        raise FileExistsError("encrypted target already exists")
    deadline = time.monotonic() + timeout_seconds
    chunks = queue.Queue(maxsize=8)
    stopped = threading.Event()
    failed = threading.Event()
    stderr_digest = hashlib.sha256()
    stderr_count = [0]
    process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

    def publish(value):
        while not stopped.is_set():
            try:
                chunks.put(value, timeout=.05)
                return
            except queue.Full:
                continue

    def stdout_reader():
        try:
            while not stopped.is_set():
                block = process.stdout.read(65536)
                if not block:
                    publish(None)
                    return
                publish(block)
        except BaseException:
            failed.set()

    def stderr_reader():
        try:
            while not stopped.is_set():
                block = process.stderr.read(65536)
                if not block:
                    return
                stderr_count[0] += len(block)
                if stderr_count[0] > max_stderr_bytes:
                    failed.set()
                    return
                stderr_digest.update(block)
        except BaseException:
            failed.set()

    readers = [threading.Thread(target=stdout_reader, daemon=True),
               threading.Thread(target=stderr_reader, daemon=True)]

    class CommandStream:
        pending = b""

        def read(self, count):
            while not self.pending:
                remaining = deadline - time.monotonic()
                if failed.is_set() or remaining <= 0:
                    raise RuntimeError("command capture failed")
                try:
                    value = chunks.get(timeout=min(.05, remaining))
                except queue.Empty:
                    continue
                if value is None:
                    return b""
                self.pending = value
            result, self.pending = self.pending[:count], self.pending[count:]
            return result

    succeeded = False
    try:
        for reader in readers:
            reader.start()
        result = encrypt_stream(CommandStream(), destination, key, format_version=format_version,
                                max_plaintext_bytes=max_plaintext_bytes)
        process.wait(timeout=max(.001, deadline - time.monotonic()))
        for reader in readers:
            reader.join(timeout=max(0, deadline - time.monotonic()))
        if (process.returncode != 0 or failed.is_set() or any(reader.is_alive() for reader in readers)
                or time.monotonic() >= deadline):
            raise RuntimeError("command capture failed")
        result.update(stderr_bytes=stderr_count[0], stderr_sha256=stderr_digest.hexdigest(),
                      child_exit_code=process.returncode, capture_readers_joined=True)
        succeeded = True
        return result
    finally:
        stopped.set()
        if not succeeded and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        cleanup_deadline = time.monotonic() + 2
        for reader in readers:
            if reader.ident is not None:
                reader.join(timeout=max(0, cleanup_deadline - time.monotonic()))
        # Closing a buffered pipe can wait on a live reader lock. Leave a
        # pending reader for process teardown instead of blocking this caller.
        for pipe, reader in zip((process.stdout, process.stderr), readers):
            if not reader.is_alive():
                pipe.close()


def _apply_and_compare_windows_acl(path: Path, sddl: str) -> str:
    """Apply captured ACL as explicit rules and compare effective semantics.

    A restored file lives below a new protected parent, so inherited ACEs from
    the original parent cannot remain inherited.  Convert those ACEs to
    explicit entries, then compare owner, group, SID, type, rights, inheritance
    flags and propagation flags while deliberately ignoring only IsInherited.
    """
    if os.name != "nt":
        raise RuntimeError("Windows ACL restore verification is required")
    powershell = Path(
        shutil.which("pwsh.exe")
        or shutil.which("pwsh")
        or str(
            Path(os.environ.get("SystemRoot", r"C:\Windows"))
            / r"System32\WindowsPowerShell\v1.0\powershell.exe"
        )
    )
    script = r"""
$ErrorActionPreference='Stop'
function Convert-CanonicalAcl($acl) {
    $rules = @($acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier]) |
        ForEach-Object {
            ('{0}|{1}|{2}|{3}|{4}' -f $_.IdentityReference.Value,
                [int]$_.AccessControlType, [int]$_.FileSystemRights,
                [int]$_.InheritanceFlags, [int]$_.PropagationFlags)
        } | Sort-Object)
    return (($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value) + ';' +
        ($acl.GetGroup([Security.Principal.SecurityIdentifier]).Value) + ';' +
        ($rules -join ';'))
}
$sourceAcl = [Security.AccessControl.FileSecurity]::new()
$sourceAcl.SetSecurityDescriptorSddlForm($env:HERMES_RESTORE_ACL_SDDL)
$restoreAcl = [Security.AccessControl.FileSecurity]::new()
$restoreAcl.SetSecurityDescriptorSddlForm($env:HERMES_RESTORE_ACL_SDDL)
$restoreAcl.SetAccessRuleProtection($true, $true)
Set-Acl -LiteralPath $env:HERMES_RESTORE_ACL_PATH -AclObject $restoreAcl
$observedAcl = Get-Acl -LiteralPath $env:HERMES_RESTORE_ACL_PATH
[pscustomobject]@{
    source = Convert-CanonicalAcl $sourceAcl
    observed = Convert-CanonicalAcl $observedAcl
    observed_protected = $observedAcl.AreAccessRulesProtected
} | ConvertTo-Json -Compress
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    child_env = os.environ.copy()
    child_env["HERMES_RESTORE_ACL_PATH"] = str(path)
    child_env["HERMES_RESTORE_ACL_SDDL"] = sddl
    process = subprocess.run(
        [str(powershell), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
        env=child_env,
    )
    if process.returncode:
        detail = (process.stderr or process.stdout or "no diagnostic output").strip()
        detail = detail.replace(str(path), "<isolated-restore-file>")[:1000]
        raise RuntimeError(f"isolated ACL restore command failed: {detail}")
    output = process.stdout.strip()
    if not output:
        raise RuntimeError("isolated ACL restore returned no descriptor")
    result = json.loads(output)
    if result.get("source") != result.get("observed"):
        raise RuntimeError("restored configuration ACL effective rules differ")
    if not result.get("observed_protected"):
        raise RuntimeError("restored configuration ACL is not protected")
    return hashlib.sha256(str(result["observed"]).encode()).hexdigest()


def _make_private_restore_root(path: Path, owner_sid: str) -> None:
    path.mkdir()
    process = subprocess.run(
        [
            "icacls.exe",
            str(path),
            "/inheritance:r",
            "/grant:r",
            f"*{owner_sid}:(OI)(CI)F",
            "SYSTEM:(OI)(CI)F",
        ],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode:
        raise RuntimeError("isolated ACL restore root hardening failed")


_HOME_INVENTORY_SCHEMA = "hermes-home-source-inventory/v1"
_HOME_INVENTORY_LIMIT = 20000
_EXCLUDED_HOME_DIRECTORIES = {
    "cache", "caches", ".cache", "__pycache__", "audio_cache", "image_cache",
    "logs", "log", "backups", "node_modules", "venv", ".venv",
}


def _home_policy(relative: str, kind: str) -> tuple[str, str]:
    name = relative.rsplit("/", 1)[-1].casefold()
    if kind == "directory":
        if relative.casefold() == "hermes-agent":
            return "exclude_subtree", "agent_source_and_runtime_have_separate_recovery_scope"
        if name in _EXCLUDED_HOME_DIRECTORIES:
            return "exclude_subtree", "cache_log_backup_or_dependency_subtree"
        return "preserve_directory", "required_directory_and_acl"
    if name.endswith((".lock", ".pid")):
        return "exclude_transient", "stale_lock_or_pid_must_not_be_activated_on_restore"
    if relative.casefold() == "models_dev_cache.json":
        return "exclude_cache", "reconstructable_model_catalog_cache"
    if name.endswith((".db", ".sqlite", ".sqlite3")):
        return "sqlite_online_backup", "consistent_online_database_image"
    if name.endswith(("-wal", "-shm")):
        if not name[:-4].endswith((".db", ".sqlite", ".sqlite3")):
            raise ValueError("unclassified database sidecar")
        return "sqlite_sidecar", "covered_by_parent_database_online_snapshot"
    return "keep_encrypted", "required_source_file_preserved_by_default"


def inventory_home(home: Path) -> dict[str, object]:
    """Inventory metadata only; excluded directories are never traversed.

    Unknown regular files/directories are preserved by default. Reparse points,
    unsupported file types and excessive inventories stop collection explicitly.
    No file values, database content, configuration or credential bytes are read.
    """
    if getattr(home.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("reparse source root is not admitted")
    home = home.resolve(strict=True)
    pending = [home]
    entries = []
    while pending:
        parent = pending.pop()
        with os.scandir(parent) as children:
            for child in children:
                info = child.stat(follow_symlinks=False)
                if child.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError("reparse source entry is not admitted")
                if stat.S_ISDIR(info.st_mode):
                    kind = "directory"
                elif stat.S_ISREG(info.st_mode):
                    kind = "file"
                else:
                    raise ValueError("unsupported source entry type")
                relative = Path(child.path).relative_to(home).as_posix()
                disposition, reason = _home_policy(relative, kind)
                entries.append(dict(relative_path=relative,
                    relative_path_sha256=hashlib.sha256(relative.encode()).hexdigest(),
                    kind=kind, disposition=disposition, reason=reason,
                    source_size_bytes=info.st_size if disposition == "keep_encrypted" else None,
                    source_modified_ns=info.st_mtime_ns if disposition == "keep_encrypted" else None))
                if len(entries) > _HOME_INVENTORY_LIMIT:
                    raise ValueError("source inventory entry limit exceeded")
                if kind == "directory" and disposition != "exclude_subtree":
                    pending.append(Path(child.path))
    entries.sort(key=lambda entry: entry["relative_path"])
    return dict(schema=_HOME_INVENTORY_SCHEMA, maximum_entries=_HOME_INVENTORY_LIMIT,
                entries=entries, excluded_subtrees_not_traversed=True)


def _run_reference(run_root: Path, reference: object) -> Path:
    if type(reference) is not str or not reference:
        raise ValueError("invalid run reference")
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("reference escapes run root")
    target = (run_root / candidate).resolve(strict=True)
    if not target.is_relative_to(run_root) or not target.is_file():
        raise ValueError("reference escapes run root")
    return target


def _read_pinned_sidecar(run_root: Path, reference: object, expected: object) -> dict:
    if not _valid_hash(expected):
        raise ValueError("invalid sidecar hash")
    path = _run_reference(run_root, reference)
    with path.open("rb") as stream:
        raw = stream.read(64 * 1024**2 + 1)
    if len(raw) > 64 * 1024**2 or not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), expected):
        raise ValueError("sidecar hash mismatch")
    result = json.loads(raw.decode("utf-8"))
    if type(result) is not dict:
        raise ValueError("invalid sidecar object")
    return result


def _check_acl_metadata(value: dict) -> str:
    sddl = value.get("source_acl_sddl")
    if (type(sddl) is not str or not sddl or len(sddl) > 65536
            or hashlib.sha256(sddl.encode()).hexdigest() != value.get("source_acl_sddl_sha256")):
        raise ValueError("source ACL metadata mismatch")
    return sddl


_COVERAGE_FAILURE_CONTEXTS = {
    "TARGET_FIELDS": ("COVERAGE_MANIFEST", "TARGET_FIELDS"),
    "INVENTORY_REFERENCE": ("COVERAGE_MANIFEST", "INVENTORY_REFERENCE"),
    "INVENTORY_REQUIRED": ("COVERAGE_CAPTURED", "INVENTORY_REQUIRED"),
    "INVENTORY_READ_OR_PIN": ("COVERAGE_CAPTURED", "INVENTORY_READ_OR_PIN"),
    "INVENTORY_SHAPE": ("COVERAGE_CAPTURED", "INVENTORY_SHAPE"),
    "INVENTORY_ACL": ("COVERAGE_CAPTURED", "INVENTORY_ACL"),
    "INVENTORY_ENTRY": ("COVERAGE_CAPTURED", "INVENTORY_ENTRY"),
    "INVENTORY_PATH": ("COVERAGE_CAPTURED", "INVENTORY_PATH"),
    "INVENTORY_POLICY": ("COVERAGE_CAPTURED", "INVENTORY_POLICY"),
    "PAYLOAD_MAPPING": ("COVERAGE_CAPTURED", "PAYLOAD_MAPPING"),
    "DATABASE_MAPPING": ("COVERAGE_CAPTURED", "DATABASE_MAPPING"),
    "LIVE_SOURCE_PROBE": ("COVERAGE_LIVE", "LIVE_SOURCE_PROBE"),
    "LIVE_INVENTORY_READ": ("COVERAGE_LIVE", "LIVE_INVENTORY_READ"),
    "LIVE_INVENTORY_CHANGED": ("COVERAGE_LIVE", "LIVE_INVENTORY_CHANGED"),
    "UNCLASSIFIED": ("COVERAGE_PRECHECK", "UNCLASSIFIED"),
}


def _tag_coverage_failure(error: Exception, subcode: str) -> Exception:
    # Preserve the original exception type/message and all rejection behavior.
    # Only the fixed allowlisted identifiers may reach public diagnostics.
    try:
        error._hermes_coverage_subcode = subcode
    except Exception:
        pass
    return error


def _coverage_call(subcode: str, function, *args):
    try:
        return function(*args)
    except Exception as error:
        _tag_coverage_failure(error, subcode)
        raise


def _coverage_invalid(subcode: str, message: str) -> ValueError:
    error = ValueError(message)
    _tag_coverage_failure(error, subcode)
    return error


def _public_coverage_failure(error: Exception) -> dict[str, str]:
    subcode = getattr(error, "_hermes_coverage_subcode", None)
    if type(subcode) is not str or subcode not in _COVERAGE_FAILURE_CONTEXTS:
        return {}
    stage, fixed_subcode = _COVERAGE_FAILURE_CONTEXTS[subcode]
    return {"error_stage": stage, "error_subcode": fixed_subcode}


def _verify_home_coverage_impl(run_root: Path, manifest: dict, items: list, *, legacy: bool,
                               check_live_source: bool = True) -> dict:
    home = _coverage_call("TARGET_FIELDS", lambda: Path(manifest["exact_targets"]["hermes_home"]))
    home_items = [item for item in items if item.get("category") == "hermes-home-file"]
    declared = manifest.get("home_source_inventory")
    if declared is None:
        if not legacy:
            raise _coverage_invalid("INVENTORY_REQUIRED", "required home source inventory is missing")
        # An old payload can still be authenticated, but an absent coverage
        # inventory can never establish a complete new backup or formal Gate.
        return dict(complete=False, required_files=0, required_directories=0,
                    state="LEGACY_COVERAGE_UNKNOWN", source_remeasured=False)
    if type(declared) is not dict:
        raise _coverage_invalid("INVENTORY_REFERENCE", "invalid home source inventory mapping")
    inventory = _coverage_call("INVENTORY_READ_OR_PIN", _read_pinned_sidecar,
                              run_root, declared.get("path"), declared.get("sha256"))
    entries = inventory.get("entries")
    if (inventory.get("schema") != _HOME_INVENTORY_SCHEMA or type(entries) is not list
            or len(entries) > _HOME_INVENTORY_LIMIT
            or inventory.get("excluded_subtrees_not_traversed") is not True):
        raise _coverage_invalid("INVENTORY_SHAPE", "invalid home source inventory")
    _coverage_call("INVENTORY_ACL", _check_acl_metadata, inventory)
    by_path = {}
    required_directories = 0
    for entry in entries:
        if type(entry) is not dict:
            raise _coverage_invalid("INVENTORY_ENTRY", "invalid source inventory entry")
        relative = entry.get("relative_path")
        if (type(relative) is not str or not relative or "\\" in relative
                or Path(relative).is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/"))
                or relative in by_path or entry.get("kind") not in {"file", "directory"}
                or hashlib.sha256(relative.encode()).hexdigest() != entry.get("relative_path_sha256")):
            raise _coverage_invalid("INVENTORY_PATH", "invalid source inventory path")
        disposition, reason = _home_policy(relative, entry["kind"])
        if entry.get("disposition") != disposition or entry.get("reason") != reason:
            raise _coverage_invalid("INVENTORY_POLICY", "source inventory disposition mismatch")
        if disposition in {"keep_encrypted", "preserve_directory"}:
            _coverage_call("INVENTORY_ACL", _check_acl_metadata, entry)
        if disposition == "preserve_directory":
            required_directories += 1
        by_path[relative] = entry
    # Captured verification must not probe the historical source locator. Its
    # existence, contents and current inventory are deliberately unobserved.
    if check_live_source and _coverage_call("LIVE_SOURCE_PROBE", home.exists):
        observed = _coverage_call("LIVE_INVENTORY_READ", inventory_home, home)
        fields = ("relative_path", "relative_path_sha256", "kind", "disposition", "reason",
                  "source_size_bytes", "source_modified_ns")
        expected_rows = sorted(tuple(entry.get(field) for field in fields) for entry in entries)
        observed_rows = sorted(tuple(entry.get(field) for field in fields) for entry in observed["entries"])
        if expected_rows != observed_rows:
            raise _coverage_invalid("LIVE_INVENTORY_CHANGED", "current home source inventory differs from captured coverage")
        remeasured = True
    else:
        remeasured = False
    required = {path: entry for path, entry in by_path.items() if entry["disposition"] == "keep_encrypted"}
    backed_up = {}
    for item in home_items:
        relative = item.get("relative_path")
        if relative in backed_up or relative not in required:
            raise _coverage_invalid("PAYLOAD_MAPPING", "unexpected or duplicate home source object")
        entry = required[relative]
        if (item.get("plaintext_bytes") != entry.get("source_size_bytes")
                or _coverage_call("INVENTORY_ACL", _check_acl_metadata, item)
                != _coverage_call("INVENTORY_ACL", _check_acl_metadata, entry)):
            raise _coverage_invalid("PAYLOAD_MAPPING", "home source size or ACL coverage mismatch")
        backed_up[relative] = item
    if set(backed_up) != set(required):
        raise _coverage_invalid("PAYLOAD_MAPPING", "required home source file is not backed up")
    databases = {item.get("source_relative_path") for item in items
                 if item.get("category") == "sqlite-online-backup"}
    required_databases = {path for path, entry in by_path.items() if entry["disposition"] == "sqlite_online_backup"}
    if databases != required_databases:
        raise _coverage_invalid("DATABASE_MAPPING", "required online database coverage mismatch")
    for path, entry in by_path.items():
        if entry["disposition"] == "sqlite_sidecar" and path[:-4] not in required_databases:
            raise _coverage_invalid("DATABASE_MAPPING", "database sidecar lacks a covered parent database")
    return dict(complete=True, required_files=len(required), required_directories=required_directories,
                required_databases=len(required_databases), state="SOURCE_INVENTORY_COVERED",
                source_remeasured=remeasured, inventory_entries=len(entries))


def _verify_home_coverage(run_root: Path, manifest: dict, items: list, *, legacy: bool,
                          check_live_source: bool = True) -> dict:
    try:
        return _verify_home_coverage_impl(run_root, manifest, items, legacy=legacy,
                                          check_live_source=check_live_source)
    except Exception as error:
        if not _public_coverage_failure(error):
            _tag_coverage_failure(error, "UNCLASSIFIED")
        raise


def _verify_run_impl(run_root: Path, manifest_path: Path, key: bytes, *,
               expected_manifest_sha256: str,
               allow_legacy_heb1: bool = False,
               max_plaintext_bytes: int | None = None,
               memory_budget_bytes: int = DEFAULT_MEMORY_BUDGET_BYTES,
               captured_only: bool = False) -> dict[str, object]:
    """Verify against an explicit caller-trusted manifest hash.

    The expected hash must come from the approved run/receipt, never from a
    replaceable adjacent checksum file. This function verifies that binding;
    it cannot certify the external authority that supplied it.
    """
    if not _valid_hash(expected_manifest_sha256) or type(allow_legacy_heb1) is not bool:
        raise ValueError("invalid trusted manifest request")
    plain_limit, _ = _operation_limit(max_plaintext_bytes)
    run_root = run_root.resolve(strict=True)
    with manifest_path.resolve(strict=True).open("rb") as stream:
        manifest_bytes = stream.read(64 * 1024**2 + 1)
    if (len(manifest_bytes) > 64 * 1024**2
            or not hmac.compare_digest(hashlib.sha256(manifest_bytes).hexdigest(), expected_manifest_sha256)):
        raise ValueError("trusted manifest hash mismatch")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    del manifest_bytes
    items = manifest.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("manifest has no items")
    for item in items:
        if item.get("payload_format") != "HEB2" and not (
                allow_legacy_heb1 and item.get("payload_format") in {None, "HEB1"}):
            raise ValueError("payload format is not admitted")
    legacy_coverage = allow_legacy_heb1 and all(item.get("payload_format") in {None, "HEB1"} for item in items)
    home_coverage = _verify_home_coverage(run_root, manifest, items, legacy=legacy_coverage,
                                          check_live_source=not captured_only)
    counts: dict[str, int] = {}
    restored_paths: set[str] = set()
    acl_restore_root = run_root / "isolated-acl-restore"
    _make_private_restore_root(acl_restore_root, str(manifest["recovery"]["key_owner_sid"]))
    acl_checks = 0
    configuration_acl_checks = 0
    restored_acl_hashes: set[str] = set()
    owned_witnesses: dict[Path, tuple[object, tuple[int, int] | None]] = {}
    legacy_heb1_items = 0
    remote_payload: bytes | None = None
    ignored_path_payload: bytes | None = None
    try:
        for item in items:
            category = str(item["category"])
            logical = str(item.get("relative_path") or item.get("backup_label"))
            if logical in restored_paths and category != "sqlite-online-backup":
                raise ValueError("duplicate logical restore path")
            restored_paths.add(logical)
            counts[category] = counts.get(category, 0) + 1
            object_ref = item.get("backup_object")
            report_ref = item.get("verification_report")
            if not object_ref or not report_ref:
                raise ValueError("manifest item lacks restore mapping")
            payload = _run_reference(run_root, object_ref)
            report_path = _run_reference(run_root, report_ref)
            with report_path.open("rb") as stream:
                report_bytes = stream.read(1024 * 1024 + 1)
            if len(report_bytes) > 1024 * 1024:
                raise ValueError("verification report too large")
            report = json.loads(report_bytes.decode("utf-8"))
            item_format = item.get("payload_format")
            report_format = report.get("payload_format")
            if item_format is not None and report_format is not None and item_format != report_format:
                raise ValueError("manifest and report payload formats differ")
            expected_format = item_format if item_format is not None else report_format
            if expected_format is None and allow_legacy_heb1:
                expected_format = "HEB1"
            if expected_format != "HEB2" and not (allow_legacy_heb1 and expected_format == "HEB1"):
                raise ValueError("payload format is not admitted")
            expected = item.get("plaintext_sha256")
            expected_cipher = item.get("ciphertext_sha256")
            expected_bytes = item.get("plaintext_bytes")
            if (not _valid_hash(expected) or not _valid_hash(expected_cipher)
                    or type(expected_bytes) is not int or not 0 <= expected_bytes <= plain_limit
                    or report.get("plaintext_sha256") != expected
                    or report.get("ciphertext_sha256") != expected_cipher
                    or report.get("plaintext_bytes") != expected_bytes):
                raise ValueError("manifest payload pins are invalid or inconsistent")
            _memory_admission(expected_bytes, memory_budget_bytes)
            if "ciphertext_bytes" in item and item["ciphertext_bytes"] != report.get("ciphertext_bytes"):
                raise ValueError("manifest ciphertext size mismatch")
            if (type(report.get("ciphertext_bytes")) is not int
                    or payload.stat().st_size != report["ciphertext_bytes"]):
                raise ValueError("encrypted payload size mismatch")
            restored, payload_format = _decrypt_bytes_with_format(payload, key,
                expected_format=expected_format, expected_ciphertext_sha256=expected_cipher,
                expected_plaintext_sha256=expected, expected_plaintext_bytes=expected_bytes,
                max_plaintext_bytes=plain_limit)
            if payload_format == "HEB1":
                legacy_heb1_items += 1
            digest = hashlib.sha256(restored).hexdigest()
            if digest != expected or digest != str(report.get("plaintext_sha256", "")):
                raise RuntimeError("restored payload hash mismatch")
            if category == "hermes-home-file":
                sddl = _check_acl_metadata(item)
                acl_hash = item["source_acl_sddl_sha256"]
                if acl_hash not in restored_acl_hashes:
                    restore_file = acl_restore_root / (acl_hash + ".tmp")
                    # Register ownership only after exclusive creation succeeds.
                    # Keep the handle open during ACL checking. Empty witnesses
                    # are retained for audit; this verifier deletes no paths.
                    witness = restore_file.open("xb")
                    owned_witnesses[restore_file] = (witness, None)
                    identity = os.fstat(witness.fileno())
                    if not stat.S_ISREG(identity.st_mode) or not identity.st_ino:
                        raise RuntimeError("ACL witness identity is unavailable")
                    owned_witnesses[restore_file] = (witness, (identity.st_dev, identity.st_ino))
                    _apply_and_compare_windows_acl(restore_file, sddl)
                    restored_acl_hashes.add(acl_hash)
                acl_checks += 1
                if logical in {"config.yaml", ".env"}:
                    configuration_acl_checks += 1
                if logical == "config.yaml":
                    import yaml
                    if not isinstance(yaml.safe_load(restored.decode("utf-8")), dict):
                        raise ValueError("restored config is not a mapping")
            if category == "source-capture" and logical == "head.zip":
                with zipfile.ZipFile(io.BytesIO(restored)) as archive:
                    if archive.testzip() is not None or not archive.namelist():
                        raise RuntimeError("restored source archive is invalid")
            if category == "source-capture" and logical.endswith(".patch"):
                restored.decode("utf-8")
            if category == "git-recovery-metadata" and logical == "git.remote-v":
                remote_payload = restored
            if category == "git-recovery-metadata" and logical == "git.ignored-path-map":
                ignored_path_payload = restored
            if category == "sqlite-online-backup":
                image = restored
                if len(image) >= 20 and (image[18] == 2 or image[19] == 2):
                    image = bytearray(restored)
                    del restored
                    image[18] = 1
                    image[19] = 1
                connection = sqlite3.connect(":memory:")
                try:
                    connection.deserialize(image)
                    del image
                    observed = inspect_db(connection)
                finally:
                    connection.close()
                for field in ("integrity", "user_version", "schema_object_counts", "schema_sha256"):
                    if observed[field] != report[field]:
                        raise RuntimeError("restored SQLite report mismatch")
    finally:
        ownership_unknown = False
        try:
            if set(acl_restore_root.iterdir()) != set(owned_witnesses):
                ownership_unknown = True
            for path, (witness, identity) in owned_witnesses.items():
                observed = path.lstat()
                if (identity is None or not stat.S_ISREG(observed.st_mode)
                        or getattr(observed, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
                        or (observed.st_dev, observed.st_ino) != identity or observed.st_size != 0):
                    ownership_unknown = True
        except Exception:
            ownership_unknown = True
        finally:
            for witness, _identity in owned_witnesses.values():
                witness.close()
        if ownership_unknown:
            raise RuntimeError("ACL witness ownership or unexpected entries are UNKNOWN; all entries retained")
    if home_coverage["complete"] and acl_checks != home_coverage["required_files"]:
        raise RuntimeError("required home file ACL metadata was not verified")
    if remote_payload is None:
        raise RuntimeError("encrypted remote recovery metadata missing")
    remote_lines = remote_payload.decode("utf-8").splitlines()
    remote_hashes = [hashlib.sha256(line.encode()).hexdigest() for line in remote_lines]
    if remote_hashes != manifest["source_git_metadata"]["remote_v_hashes"]:
        raise RuntimeError("restored remote metadata does not match public hashes")
    if ignored_path_payload is None:
        raise RuntimeError("encrypted ignored path map missing")
    ignored_paths = [part.decode("utf-8") for part in ignored_path_payload.split(b"\0") if part]
    ignored_meta = manifest["source_git_metadata"]
    for reference_name in ("encrypted_remote_metadata", "encrypted_ignored_path_map"):
        if reference_name in ignored_meta:
            _run_reference(run_root, ignored_meta[reference_name])
    filtered = _read_pinned_sidecar(run_root, ignored_meta["secret_filtered_ignored_inventory"],
                                    ignored_meta["secret_filtered_ignored_inventory_sha256"])
    if len(ignored_paths) > int(filtered["maximum_entries"]):
        raise RuntimeError("ignored inventory exceeded declared bound")
    tokens = [hashlib.sha256(path.replace("\\", "/").encode()).hexdigest() for path in ignored_paths]
    filtered_tokens = [str(entry["path_sha256"]) for entry in filtered["entries"]]
    if len(tokens) != filtered["source_count"] or sorted(set(tokens)) != sorted(filtered_tokens):
        raise RuntimeError("secret-filtered ignored inventory does not cover encrypted path map")
    observed_decisions: dict[str, int] = {
        str(reason): 0 for reason in filtered["decision_counts"]
    }
    kept_tokens: set[str] = set()
    for entry in filtered["entries"]:
        reason = str(entry["reason"])
        observed_decisions[reason] = observed_decisions.get(reason, 0) + 1
        if entry["decision"] == "keep_encrypted":
            kept_tokens.add(str(entry["path_sha256"]))
        elif entry["decision"] != "exclude":
            raise RuntimeError("unsupported ignored inventory decision")
    if observed_decisions != filtered["decision_counts"] or observed_decisions != ignored_meta["ignored_decision_counts"]:
        raise RuntimeError("ignored keep/exclude decision counts mismatch")
    backed_up_ignored = {
        str(item["source_path_sha256"])
        for item in items if item["category"] == "hermes-agent-ignored-required"
    }
    if kept_tokens != backed_up_ignored:
        raise RuntimeError("ignored recovery candidates are not fully encrypted")
    required = {"source-capture", "hermes-agent-dirty-file", "hermes-home-file", "sqlite-online-backup", "git-recovery-metadata"}
    if not required.issubset(counts):
        raise ValueError("required restore categories missing")
    result = {
        "status": "ok" if home_coverage["complete"] else "legacy_payloads_verified_coverage_unknown",
        "mode": "in-memory payload restore; empty private witnesses verify distinct file ACL descriptors",
        "item_count": len(items),
        "legacy_heb1_items": legacy_heb1_items,
        "manifest_sha256": expected_manifest_sha256,
        "manifest_authority": "caller supplied; external authority is not certified here",
        "legacy_integrity_note": "HEB1 requires explicit opt-in plus whole-payload hashes and length bound to the caller-trusted manifest",
        "category_counts": counts,
        "logical_path_count": len(restored_paths),
        "home_source_coverage": home_coverage,
        "home_file_acl_metadata_verified": acl_checks,
        "distinct_file_acl_restore_checks": len(restored_acl_hashes),
        "configuration_acl_files_restored_and_matched": configuration_acl_checks,
        "credential_or_config_plaintext_persisted": False,
        "isolated_acl_witness_cleanup": "retained_empty_witnesses_no_deletion",
        "retained_empty_acl_witnesses": len(owned_witnesses),
        "remote_metadata_restore_and_hash_match": "ok",
        "ignored_inventory_bound": filtered["maximum_entries"],
        "ignored_inventory_entries_verified": len(tokens),
        "ignored_inventory_decision_counts": observed_decisions,
        "source_archive_parse": "ok",
        "patch_utf8_parse": "ok",
        "config_yaml_parse": "ok",
        "sqlite_integrity_schema_user_version": "ok",
    }
    if captured_only:
        result.update(_captured_scope_report())
        result["status"] = ("historical_capture_verified" if home_coverage["complete"]
                            else "historical_payloads_verified_coverage_unknown")
        result["mode"] = "captured-only in-memory restore; historical inventory and ACL descriptors"
        # 'complete' refers only to the pinned ledger's required-item mapping,
        # not to source freshness or point-in-time consistency.
        home_coverage.update(state=("CAPTURED_INVENTORY_COVERED" if home_coverage["complete"]
                                    else "LEGACY_COVERAGE_UNKNOWN"),
                             coverage_basis="caller-trusted captured inventory only",
                             live_coverage="UNKNOWN", source_remeasured=False)
    return result


def _captured_scope_report() -> dict[str, object]:
    return {"verification_scope": "historical_capture_only", "historical_only": True,
            "historical_source_state": "captured_manifest_and_inventory_only",
            "live_coverage": "UNKNOWN", "live_source_observed": False,
            "point_in_time_coherence": "NOT_ESTABLISHED", "gate_pass": False}


def verify_run(run_root: Path, manifest_path: Path, key: bytes, *,
               expected_manifest_sha256: str,
               allow_legacy_heb1: bool = False,
               max_plaintext_bytes: int | None = None,
               memory_budget_bytes: int = DEFAULT_MEMORY_BUDGET_BYTES) -> dict[str, object]:
    """Original full verifier: the live inventory check remains mandatory if present."""
    return _verify_run_impl(run_root, manifest_path, key,
        expected_manifest_sha256=expected_manifest_sha256, allow_legacy_heb1=allow_legacy_heb1,
        max_plaintext_bytes=max_plaintext_bytes, memory_budget_bytes=memory_budget_bytes)


def verify_captured(run_root: Path, manifest_path: Path, key: bytes, *,
                    expected_manifest_sha256: str,
                    allow_legacy_heb1: bool = False,
                    max_plaintext_bytes: int | None = None,
                    memory_budget_bytes: int = DEFAULT_MEMORY_BUDGET_BYTES) -> dict[str, object]:
    """Authenticate captured artifacts only; never establishes live coverage/Gate PASS.

    Use only a separately authorized isolated copy. Manifest bytes, caller-trusted
    hash, source locators and all required mappings remain unchanged. The original
    failed run stays failed; this is a new historical-only observation, not a retry
    of its live-source acceptance decision. No live source path is inspected.
    """
    return _verify_run_impl(run_root, manifest_path, key,
        expected_manifest_sha256=expected_manifest_sha256, allow_legacy_heb1=allow_legacy_heb1,
        max_plaintext_bytes=max_plaintext_bytes, memory_budget_bytes=memory_budget_bytes,
        captured_only=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init-key")
    p_init.add_argument("--key-file", required=True, type=Path)
    p_inventory = sub.add_parser("inventory-home")
    p_inventory.add_argument("--source", required=True, type=Path)
    p_inventory.add_argument("--report", required=True, type=Path)
    p_file = sub.add_parser("encrypt-file")
    p_file.add_argument("--key-file", required=True, type=Path)
    p_file.add_argument("--source", required=True, type=Path)
    p_file.add_argument("--destination", required=True, type=Path)
    p_file.add_argument("--report", required=True, type=Path)
    p_file.add_argument("--payload-format", choices=("HEB1", "HEB2"), default="HEB2")
    p_command = sub.add_parser("encrypt-command")
    p_command.add_argument("--key-file", required=True, type=Path)
    p_command.add_argument("--destination", required=True, type=Path)
    p_command.add_argument("--report", required=True, type=Path)
    p_command.add_argument("--cwd", required=True, type=Path)
    p_command.add_argument("--payload-format", choices=("HEB1", "HEB2"), default="HEB2")
    p_command.add_argument("--timeout-seconds", type=float, default=120)
    p_command.add_argument("--max-stderr-bytes", type=int, default=1024 * 1024)
    p_command.add_argument("argv", nargs=argparse.REMAINDER)
    p_sqlite = sub.add_parser("sqlite-backup")
    p_sqlite.add_argument("--key-file", required=True, type=Path)
    p_sqlite.add_argument("--source", required=True, type=Path)
    p_sqlite.add_argument("--destination", required=True, type=Path)
    p_sqlite.add_argument("--report", required=True, type=Path)
    p_sqlite.add_argument("--payload-format", choices=("HEB1", "HEB2"), default="HEB2")
    p_sqlite.add_argument("--timeout-seconds", type=float, default=120)
    p_verify = sub.add_parser("verify-run")
    p_captured = sub.add_parser("verify-captured", help="historical only; live coverage UNKNOWN; never Gate PASS")
    for command_parser in (p_verify, p_captured):
        command_parser.add_argument("--key-file", required=True, type=Path)
        command_parser.add_argument("--manifest", required=True, type=Path)
        command_parser.add_argument("--run-root", required=True, type=Path)
        command_parser.add_argument("--report", required=True, type=Path)
        command_parser.add_argument("--expected-manifest-sha256", required=True)
        command_parser.add_argument("--allow-legacy-heb1", action="store_true")
    for command_parser in (p_file, p_command, p_sqlite, p_verify, p_captured):
        command_parser.add_argument("--max-plaintext-bytes", type=int)
    for command_parser in (p_sqlite, p_verify, p_captured):
        command_parser.add_argument("--memory-budget-bytes", type=int, default=DEFAULT_MEMORY_BUDGET_BYTES)
    args = parser.parse_args()
    try:
        if args.command == "init-key":
            init_key(args.key_file)
        elif args.command == "inventory-home":
            write_json_exclusive(args.report, inventory_home(args.source))
        else:
            key = load_key(args.key_file)
            if args.command in {"verify-run", "verify-captured"}:
                verifier = verify_captured if args.command == "verify-captured" else verify_run
                result = verifier(args.run_root, args.manifest, key,
                    expected_manifest_sha256=args.expected_manifest_sha256,
                    allow_legacy_heb1=args.allow_legacy_heb1,
                    max_plaintext_bytes=args.max_plaintext_bytes,
                    memory_budget_bytes=args.memory_budget_bytes)
            elif args.command == "encrypt-file":
                with args.source.resolve(strict=True).open("rb") as stream:
                    result = encrypt_stream(stream, args.destination, key, format_version=args.payload_format,
                                            max_plaintext_bytes=args.max_plaintext_bytes)
            elif args.command == "encrypt-command":
                argv = args.argv[1:] if args.argv and args.argv[0] == "--" else args.argv
                if not argv:
                    raise ValueError("missing command")
                result = encrypt_command(argv, args.cwd, args.destination, key,
                    format_version=args.payload_format, max_plaintext_bytes=args.max_plaintext_bytes,
                    timeout_seconds=args.timeout_seconds, max_stderr_bytes=args.max_stderr_bytes)
            else:
                result = sqlite_backup(args.source, args.destination, key, format_version=args.payload_format,
                    max_plaintext_bytes=args.max_plaintext_bytes, memory_budget_bytes=args.memory_budget_bytes,
                    timeout_seconds=args.timeout_seconds)
            write_json_exclusive(args.report, result)
        outcome = "completed_historical_only_gate_pass_false" if args.command == "verify-captured" else "ok"
        print(f"hermes_encrypted_backup_{args.command}: {outcome}")
        return 0
    except Exception as exc:
        # Public reports must not contain exception text or traceback: these may
        # include configuration plaintext, paths, SQL, or child output.
        if isinstance(exc, FileNotFoundError):
            error_code = "FILE_NOT_FOUND"
        elif isinstance(exc, FileExistsError):
            error_code = "TARGET_EXISTS"
        elif isinstance(exc, ValueError):
            error_code = "INVALID_INPUT"
        else:
            error_code = "OPERATION_FAILED"
        coverage_context = _public_coverage_failure(exc)
        report_path = getattr(args, "report", None)
        if report_path is not None and not report_path.exists():
            try:
                write_json_exclusive(report_path, {
                    "status": "failed",
                    "error_code": error_code,
                    **coverage_context,
                    **(_captured_scope_report() if args.command == "verify-captured" else {}),
                })
            except Exception:
                pass
        fixed_context = (" stage=" + coverage_context["error_stage"]
                         + " subcode=" + coverage_context["error_subcode"]) if coverage_context else ""
        print(f"hermes_encrypted_backup: failed ({error_code}){fixed_context}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
