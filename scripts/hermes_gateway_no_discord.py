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


def _resolve_project_root() -> Path:
    override = os.environ.get("HERMES_PROJECT_ROOT")
    if override:
        candidate = Path(override).expanduser()
        if candidate.exists():
            return candidate

    opt_lib = Path("/opt/homebrew/opt/hermes-agent/libexec/lib")
    opt_candidates = sorted(opt_lib.glob("python*/site-packages"))
    if opt_candidates:
        return opt_candidates[-1]

    cellar_root = Path("/opt/homebrew/Cellar/hermes-agent")
    if cellar_root.exists():
        versions = [path for path in cellar_root.iterdir() if path.is_dir()]
        if versions:
            latest = max(versions, key=lambda path: _parse_version(path.name))
            cellar_candidates = sorted((latest / "libexec" / "lib").glob("python*/site-packages"))
            if cellar_candidates:
                return cellar_candidates[-1]

    raise RuntimeError("Unable to locate Hermes site-packages. Set HERMES_PROJECT_ROOT explicitly.")


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
