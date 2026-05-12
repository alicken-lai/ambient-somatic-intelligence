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


PROJECT_ROOT = Path("/opt/homebrew/Cellar/hermes-agent/2026.5.7/libexec/lib/python3.14/site-packages")
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
