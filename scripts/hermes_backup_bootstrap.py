"""Run a pinned backup helper with pinned packages under Python -I -S -B.

No site directory is added to sys.path. Package Python modules execute from
the bytes checked against the supplied aggregate pin. PyYAML's optional native
loader is disabled. Cryptography's pinned bundled extension uses the standard
extension loader; this is not a claim of atomic OS loading or package authority.
Pins must come from the reviewed runtime manifest, not an untrusted neighbor.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import types


_HASH = re.compile(r"[0-9a-f]{64}\Z")
_MAX_PACKAGE_BYTES = 64 * 1024**2
_MAX_PACKAGE_FILES = 1024
_MAX_HELPER_BYTES = 1024**2


def _pin(value: str) -> bool:
    return type(value) is str and _HASH.fullmatch(value) is not None


def _plain_path(path: Path) -> None:
    info = path.lstat()
    if path.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("reparse path is not admitted")


def _walk_error(_error):
    raise ValueError("package traversal failed")


def snapshot_package(name: str, directory: Path, *, allow_native: bool) -> dict:
    """Return a bounded source snapshot and its deterministic package digest."""
    if name not in {"yaml", "cryptography"}:
        raise ValueError("unsupported package")
    _plain_path(directory)
    root = directory.resolve(strict=True)
    if not root.is_dir() or root.name != name:
        raise ValueError("invalid package directory")
    records, sources, extensions = [], {}, {}
    total = 0
    for parent, folders, files in os.walk(root, followlinks=False, onerror=_walk_error):
        folders[:] = sorted(folder for folder in folders if folder != "__pycache__")
        for folder in folders:
            _plain_path(Path(parent) / folder)
        for filename in sorted(files):
            native = allow_native and filename.endswith(tuple(importlib.machinery.EXTENSION_SUFFIXES))
            if not filename.endswith(".py") and not native:
                continue
            path = Path(parent) / filename
            _plain_path(path)
            if not path.is_file():
                raise ValueError("invalid package file")
            size = path.stat().st_size
            if total + size > _MAX_PACKAGE_BYTES or len(records) >= _MAX_PACKAGE_FILES:
                raise ValueError("package limit exceeded")
            with path.open("rb") as stream:
                raw = stream.read(_MAX_PACKAGE_BYTES - total + 1)
            total += len(raw)
            if len(raw) != size or total > _MAX_PACKAGE_BYTES:
                raise ValueError("package changed or exceeded its limit")
            relative = path.relative_to(root).as_posix()
            digest = hashlib.sha256(raw).hexdigest()
            records.append([relative, digest])
            if filename.endswith(".py"):
                parts = path.relative_to(root).with_suffix("").parts
                package = parts[-1] == "__init__"
                module_parts = parts[:-1] if package else parts
                if any(not part.isidentifier() for part in module_parts):
                    raise ValueError("invalid package module path")
                fullname = ".".join((name, *module_parts))
                sources[fullname] = (path, raw, package)
            else:
                suffix = next(suffix for suffix in importlib.machinery.EXTENSION_SUFFIXES
                              if filename.endswith(suffix))
                leaf = filename[:-len(suffix)]
                parts = (*path.relative_to(root).parent.parts, leaf)
                if any(not part.isidentifier() for part in parts):
                    raise ValueError("invalid extension module path")
                extensions[".".join((name, *parts))] = (path, digest)
    if name not in sources:
        raise ValueError("package initializer missing")
    records.sort()
    digest = hashlib.sha256(json.dumps(records, ensure_ascii=True,
        separators=(",", ":")).encode("ascii")).hexdigest()
    return dict(name=name, root=root, digest=digest, sources=sources,
                extensions=extensions, file_count=len(records), bytes=total)


class _SourceLoader(importlib.abc.Loader):
    def __init__(self, path: Path, raw: bytes):
        self.path, self.raw = path, raw

    def create_module(self, _spec):
        return None

    def exec_module(self, module):
        exec(compile(self.raw, str(self.path), "exec"), module.__dict__)


class _PackageFinder(importlib.abc.MetaPathFinder):
    def __init__(self, packages: list[dict], cffi_extension=None):
        self.sources = {key: value for package in packages for key, value in package["sources"].items()}
        self.extensions = {key: value for package in packages for key, value in package["extensions"].items()}
        if cffi_extension is not None:
            self.extensions["_cffi_backend"] = cffi_extension

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] not in {"yaml", "cryptography", "_cffi_backend"}:
            return None
        if fullname in {"yaml.cyaml", "yaml._yaml"}:
            raise ModuleNotFoundError("native YAML loader disabled")
        if fullname in self.sources:
            source, raw, package = self.sources[fullname]
            return importlib.util.spec_from_file_location(fullname,
                str(source), loader=_SourceLoader(source, raw),
                submodule_search_locations=[str(source.parent)] if package else None)
        if fullname in self.extensions:
            source, expected = self.extensions[fullname]
            _plain_path(source)
            with source.open("rb") as stream:
                raw = stream.read(_MAX_PACKAGE_BYTES + 1)
            if len(raw) > _MAX_PACKAGE_BYTES or hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("extension identity changed")
            return importlib.util.spec_from_file_location(fullname, str(source),
                loader=importlib.machinery.ExtensionFileLoader(fullname, str(source)))
        raise ModuleNotFoundError("module absent from pinned package")


def run_pinned(helper: Path, expected_helper: str, crypto: Path, expected_crypto: str,
               yaml: Path, expected_yaml: str, arguments: list[str], *,
               cffi_extension: Path | None = None, expected_cffi: str | None = None) -> int:
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("isolated no-site runtime required")
    if any(part.casefold() in {"site-packages", "dist-packages"}
           for value in sys.path for part in Path(value).parts):
        raise ValueError("site search directory is not admitted")
    if any(key.split(".", 1)[0] in {"yaml", "cryptography", "_cffi_backend"} for key in sys.modules):
        raise ValueError("dependency was loaded before pin verification")
    if not all(_pin(value) for value in (expected_helper, expected_crypto, expected_yaml)):
        raise ValueError("invalid expected identity")
    _plain_path(helper)
    helper = helper.resolve(strict=True)
    with helper.open("rb") as stream:
        helper_bytes = stream.read(_MAX_HELPER_BYTES + 1)
    if (len(helper_bytes) > _MAX_HELPER_BYTES
            or hashlib.sha256(helper_bytes).hexdigest() != expected_helper):
        raise ValueError("helper identity mismatch")
    packages = [snapshot_package("cryptography", crypto, allow_native=True),
                snapshot_package("yaml", yaml, allow_native=False)]
    if packages[0]["digest"] != expected_crypto or packages[1]["digest"] != expected_yaml:
        raise ValueError("package identity mismatch")
    cffi = None
    if cffi_extension is not None or expected_cffi is not None:
        if cffi_extension is None or not _pin(expected_cffi):
            raise ValueError("invalid CFFI extension identity")
        _plain_path(cffi_extension)
        cffi_extension = cffi_extension.resolve(strict=True)
        if cffi_extension.name not in {"_cffi_backend" + suffix
                                      for suffix in importlib.machinery.EXTENSION_SUFFIXES}:
            raise ValueError("invalid CFFI extension path")
        with cffi_extension.open("rb") as stream:
            raw = stream.read(_MAX_PACKAGE_BYTES + 1)
        if len(raw) > _MAX_PACKAGE_BYTES or hashlib.sha256(raw).hexdigest() != expected_cffi:
            raise ValueError("CFFI extension identity mismatch")
        cffi = (cffi_extension, expected_cffi)
    finder = _PackageFinder(packages, cffi)
    sys.meta_path.insert(0, finder)
    original_argv, original_main = sys.argv, sys.modules.get("__main__")
    namespace = types.ModuleType("__main__")
    namespace.__file__ = str(helper)
    namespace.__package__ = None
    namespace.__spec__ = None
    try:
        import cryptography
        import yaml as yaml_module
        if cryptography.__version__ != "50.0.1" or yaml_module.__version__ != "6.0.3":
            raise ValueError("dependency version mismatch")
        if yaml_module.__with_libyaml__ is not False:
            raise ValueError("native YAML loader was admitted")
        sys.argv = [str(helper), *arguments]
        sys.modules["__main__"] = namespace
        try:
            exec(compile(helper_bytes, str(helper), "exec"), namespace.__dict__)
        except SystemExit as result:
            if result.code is None:
                return 0
            return result.code if type(result.code) is int and 0 <= result.code <= 125 else 1
        return 0
    finally:
        sys.argv = original_argv
        if original_main is None:
            sys.modules.pop("__main__", None)
        else:
            sys.modules["__main__"] = original_main
        sys.meta_path.remove(finder)
        for name in list(sys.modules):
            if name.split(".", 1)[0] in {"yaml", "cryptography", "_cffi_backend"}:
                del sys.modules[name]


class _Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError("invalid bootstrap arguments")


def main(argv=None) -> int:
    try:
        parser = _Parser(description=__doc__)
        parser.add_argument("--helper", type=Path, required=True)
        parser.add_argument("--helper-sha256", required=True)
        parser.add_argument("--crypto-package", type=Path, required=True)
        parser.add_argument("--crypto-package-sha256", required=True)
        parser.add_argument("--yaml-package", type=Path, required=True)
        parser.add_argument("--yaml-package-sha256", required=True)
        parser.add_argument("--cffi-extension", type=Path)
        parser.add_argument("--cffi-extension-sha256")
        parser.add_argument("arguments", nargs=argparse.REMAINDER)
        args = parser.parse_args(argv)
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        return run_pinned(args.helper, args.helper_sha256, args.crypto_package,
            args.crypto_package_sha256, args.yaml_package,
            args.yaml_package_sha256, arguments, cffi_extension=args.cffi_extension,
            expected_cffi=args.cffi_extension_sha256)
    except Exception:
        # Paths, helper exception messages and argument values may be sensitive.
        print("hermes_backup_bootstrap: failed (BOOTSTRAP_OR_HELPER_FAILED)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
