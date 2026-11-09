"""Read-only dependency/syntax smoke for the pinned backup bootstrap.

This does not execute backup-helper handlers, DPAPI, ACL commands or backups.
The invoking bootstrap supplies the reviewed isolated dependency environment.
"""
import argparse
import hashlib
from pathlib import Path
import re
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import yaml


class _Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError("invalid preflight arguments")


def main():
    try:
        parser = _Parser(description=__doc__)
        parser.add_argument("--target-helper", required=True, type=Path)
        parser.add_argument("--target-helper-sha256", required=True)
        args = parser.parse_args()
        if re.fullmatch(r"[0-9a-f]{64}", args.target_helper_sha256) is None:
            raise ValueError("invalid helper identity")
        with args.target_helper.open("rb") as stream:
            source = stream.read(1024**2 + 1)
        if (len(source) > 1024**2
                or hashlib.sha256(source).hexdigest() != args.target_helper_sha256):
            raise ValueError("target helper identity mismatch")
        compile(source, str(args.target_helper), "exec")
        if yaml.__with_libyaml__ is not False or yaml.safe_load("synthetic: true") != {"synthetic": True}:
            raise ValueError("pure YAML dependency smoke failed")
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"synthetic",
                   info=b"backup bootstrap preflight").derive(bytes(32))
        aes, nonce = AESGCM(key), bytes(12)
        if aes.decrypt(nonce, aes.encrypt(nonce, b"synthetic", b"aad"), b"aad") != b"synthetic":
            raise ValueError("cipher dependency smoke failed")
        print("hermes_backup_preflight: ok")
        return 0
    except Exception:
        print("hermes_backup_preflight: failed (PREFLIGHT_FAILED)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
