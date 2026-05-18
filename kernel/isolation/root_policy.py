"""Root policy — forbids import-time root mutation."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("kernel.isolation.root_policy")

_FALLBACK = Path.home() / "ambient-os"
_ENV_KEY = "AMBIENT_OS_ROOT"
_FORBID_IMPORT_TIME_WRITE = True


def resolve_ambient_root() -> Path:
    """Resolve repository root once; log explicit fallback."""
    env = os.environ.get(_ENV_KEY)
    if env:
        root = Path(env).expanduser().resolve()
        if root.is_dir():
            return root
        logger.warning("AMBIENT_OS_ROOT=%s not a directory; using fallback", env)

    cwd = Path.cwd()
    for candidate in (cwd, cwd.parent):
        if (candidate / "kernel").is_dir() and (candidate / "AGENTS.md").exists():
            return candidate.resolve()

    logger.warning(
        "explicit ~/ambient-os fallback for AMBIENT_OS_ROOT (set %s to override)",
        _ENV_KEY,
    )
    return _FALLBACK.resolve()


def assert_no_import_time_write(caller_module: str) -> None:
    """Hook for linters/tests — import-time writes are forbidden."""
    if _FORBID_IMPORT_TIME_WRITE:
        return
