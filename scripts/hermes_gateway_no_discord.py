#!/usr/bin/env python3
"""Start Hermes Gateway with Discord auto-enable isolated.

Hermes loads HERMES_HOME/.env during hermes_cli.main import. This wrapper keeps
that normal load path, then removes DISCORD_BOT_TOKEN from this process only so
the gateway does not auto-enable Discord when the adapter dependency is absent.
The credential file is not modified.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _parse_version(version: str) -> tuple[int, ...]:
    parsed: list[int] = []
    for part in version.split("."):
        if not part.isdigit():
            break
        parsed.append(int(part))
    return tuple(parsed)


def _parse_python_version(name: str) -> tuple[int, ...]:
    if not name.startswith("python"):
        return ()
    return _parse_version(name.removeprefix("python"))


def _latest_site_packages(lib_root: Path) -> Path | None:
    versioned_candidates = [
        (path, _parse_python_version(path.parent.name))
        for path in lib_root.glob("python*/site-packages")
    ]
    versioned_candidates = [(path, version) for path, version in versioned_candidates if version]
    if not versioned_candidates:
        return None
    return max(versioned_candidates, key=lambda item: item[1])[0]


def _resolve_project_root() -> Path:
    override = os.environ.get("HERMES_PROJECT_ROOT")
    if override:
        candidate = Path(override).expanduser()
        if candidate.exists():
            return candidate

    opt_lib = Path("/opt/homebrew/opt/hermes-agent/libexec/lib")
    opt_candidate = _latest_site_packages(opt_lib)
    if opt_candidate:
        return opt_candidate

    cellar_root = Path("/opt/homebrew/Cellar/hermes-agent")
    if cellar_root.exists():
        versions = [path for path in cellar_root.iterdir() if path.is_dir() and _parse_version(path.name)]
        if versions:
            latest = max(versions, key=lambda path: _parse_version(path.name))
            cellar_candidate = _latest_site_packages(latest / "libexec" / "lib")
            if cellar_candidate:
                return cellar_candidate

    raise RuntimeError(
        f"Unable to locate Hermes site-packages from {opt_lib} or {cellar_root}. "
        "Set HERMES_PROJECT_ROOT explicitly."
    )


PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hermes_cli import env_loader  # noqa: E402


_real_load_hermes_dotenv = env_loader.load_hermes_dotenv


def _load_hermes_dotenv_without_discord(*args, **kwargs):
    loaded = _real_load_hermes_dotenv(*args, **kwargs)
    os.environ.pop("DISCORD_BOT_TOKEN", None)
    return loaded


env_loader.load_hermes_dotenv = _load_hermes_dotenv_without_discord

sys.argv = [
    "hermes",
    "gateway",
    "run",
    "--replace",
]

from hermes_cli.main import main  # noqa: E402


if __name__ == "__main__":
    main()
