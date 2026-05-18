"""
LaunchAgent Sampling Manager — macOS launchd integration for persistent telemetry.

Generates and manages LaunchAgent plist files for periodic telemetry
collection that survives system sleep/wake cycles.  Plist files are
generated on disk but never auto-installed; loading requires explicit
operator action (or a dry-run preview).
"""

from __future__ import annotations

import logging
import os
import plistlib
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from telemetry.sampling.sampling_policy import SamplingPolicy

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
DEFAULT_PLIST_DIR = AMBIENT_ROOT / "telemetry" / "runtime" / "launchagents"
LAUNCHAGENTS_SYSTEM_DIR = Path.home() / "Library" / "LaunchAgents"

_BUNDLE_PREFIX = "com.ambient-os.telemetry"


@dataclass
class PlistConfig:
    """Describes a generated LaunchAgent plist."""
    label: str
    plist_path: Path
    source_name: str
    start_interval: int
    keep_alive: bool
    watch_paths: list[str] = field(default_factory=list)
    throttle_interval: int = 60
    program_arguments: list[str] = field(default_factory=list)
    loaded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "plist_path": str(self.plist_path),
            "source_name": self.source_name,
            "start_interval": self.start_interval,
            "keep_alive": self.keep_alive,
            "watch_paths": self.watch_paths,
            "throttle_interval": self.throttle_interval,
            "program_arguments": self.program_arguments,
            "loaded": self.loaded,
        }


class LaunchdSamplingManager:
    """Manages launchd-based periodic sampling agents.

    Generates and manages LaunchAgent plist files for persistent
    telemetry collection, surviving system sleep/wake cycles.

    Parameters
    ----------
    plist_dir:
        Where to write generated plist files.  Defaults to
        ``telemetry/runtime/launchagents/`` inside AMBIENT_ROOT.
    python_executable:
        Path to the Python interpreter to use in plist commands.
    ambient_root:
        Root directory of the Ambient OS installation.
    """

    def __init__(
        self,
        plist_dir: Path | str | None = None,
        python_executable: str | None = None,
        ambient_root: Path | str | None = None,
    ):
        self._plist_dir = Path(plist_dir) if plist_dir else DEFAULT_PLIST_DIR
        self._python = python_executable or _detect_python()
        self._ambient_root = Path(ambient_root) if ambient_root else AMBIENT_ROOT
        self._configs: dict[str, PlistConfig] = {}

    # ── Plist generation ──────────────────────────────────────────────

    def generate_plist(
        self,
        policy: SamplingPolicy,
        sample_script: str | None = None,
        watch_paths: list[str] | None = None,
    ) -> PlistConfig:
        """Generate a LaunchAgent plist for the given policy.

        Does NOT install the plist — call ``load_agent`` explicitly.
        """
        label = f"{_BUNDLE_PREFIX}.{policy.source_name}"
        filename = f"{label}.plist"
        plist_path = self._plist_dir / filename

        script = sample_script or self._default_sample_script(policy.source_name)
        program_args = [self._python, "-c", script]

        keep_alive = policy.priority == "critical"

        plist_data = self._build_plist_dict(
            label=label,
            program_arguments=program_args,
            start_interval=policy.desired_cadence_seconds,
            keep_alive=keep_alive,
            watch_paths=watch_paths or [],
            throttle_interval=max(60, policy.desired_cadence_seconds // 5),
        )

        self._plist_dir.mkdir(parents=True, exist_ok=True)
        with open(plist_path, "wb") as fh:
            plistlib.dump(plist_data, fh)

        config = PlistConfig(
            label=label,
            plist_path=plist_path,
            source_name=policy.source_name,
            start_interval=policy.desired_cadence_seconds,
            keep_alive=keep_alive,
            watch_paths=watch_paths or [],
            throttle_interval=max(60, policy.desired_cadence_seconds // 5),
            program_arguments=program_args,
            loaded=False,
        )
        self._configs[policy.source_name] = config

        logger.info(
            "Generated plist for '%s' at %s (interval=%ds)",
            policy.source_name,
            plist_path,
            policy.desired_cadence_seconds,
        )
        return config

    def generate_all(
        self,
        policies: list[SamplingPolicy],
    ) -> list[PlistConfig]:
        """Generate plists for multiple policies."""
        return [self.generate_plist(p) for p in policies]

    # ── Load / Unload (dry-run capable) ───────────────────────────────

    def load_agent(self, source_name: str, dry_run: bool = True) -> dict[str, Any]:
        """Load a LaunchAgent via launchctl.

        When ``dry_run=True`` (default), only returns the command that
        *would* be executed without running it.
        """
        config = self._configs.get(source_name)
        if config is None:
            return {"error": f"No plist generated for '{source_name}'"}

        install_path = LAUNCHAGENTS_SYSTEM_DIR / config.plist_path.name
        cmd_copy = ["cp", str(config.plist_path), str(install_path)]
        cmd_load = ["launchctl", "load", str(install_path)]

        result: dict[str, Any] = {
            "source_name": source_name,
            "label": config.label,
            "install_path": str(install_path),
            "commands": [cmd_copy, cmd_load],
            "dry_run": dry_run,
        }

        if dry_run:
            result["status"] = "dry_run"
            logger.info("Dry-run load for '%s': %s", source_name, cmd_load)
        else:
            try:
                install_path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(cmd_copy, check=True, capture_output=True, text=True)
                subprocess.run(cmd_load, check=True, capture_output=True, text=True)
                config.loaded = True
                result["status"] = "loaded"
                logger.info("Loaded agent '%s'", source_name)
            except subprocess.CalledProcessError as exc:
                result["status"] = "error"
                result["error"] = exc.stderr
                logger.error("Failed to load agent '%s': %s", source_name, exc.stderr)

        return result

    def unload_agent(self, source_name: str, dry_run: bool = True) -> dict[str, Any]:
        """Unload a LaunchAgent via launchctl."""
        config = self._configs.get(source_name)
        if config is None:
            return {"error": f"No plist generated for '{source_name}'"}

        install_path = LAUNCHAGENTS_SYSTEM_DIR / config.plist_path.name
        cmd_unload = ["launchctl", "unload", str(install_path)]
        cmd_remove = ["rm", "-f", str(install_path)]

        result: dict[str, Any] = {
            "source_name": source_name,
            "label": config.label,
            "commands": [cmd_unload, cmd_remove],
            "dry_run": dry_run,
        }

        if dry_run:
            result["status"] = "dry_run"
        else:
            try:
                subprocess.run(cmd_unload, check=True, capture_output=True, text=True)
                subprocess.run(cmd_remove, check=True, capture_output=True, text=True)
                config.loaded = False
                result["status"] = "unloaded"
            except subprocess.CalledProcessError as exc:
                result["status"] = "error"
                result["error"] = exc.stderr

        return result

    # ── Query ─────────────────────────────────────────────────────────

    def list_agents(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._configs.values()]

    def loaded_agents(self) -> list[str]:
        return [name for name, c in self._configs.items() if c.loaded]

    def get_config(self, source_name: str) -> PlistConfig | None:
        return self._configs.get(source_name)

    def read_plist(self, source_name: str) -> dict[str, Any] | None:
        """Read and return the contents of a generated plist file."""
        config = self._configs.get(source_name)
        if config is None or not config.plist_path.exists():
            return None
        with open(config.plist_path, "rb") as fh:
            return plistlib.load(fh)

    # ── Plist construction ────────────────────────────────────────────

    @staticmethod
    def _build_plist_dict(
        label: str,
        program_arguments: list[str],
        start_interval: int,
        keep_alive: bool,
        watch_paths: list[str],
        throttle_interval: int,
    ) -> dict[str, Any]:
        plist: dict[str, Any] = {
            "Label": label,
            "ProgramArguments": program_arguments,
            "StartInterval": start_interval,
            "ThrottleInterval": throttle_interval,
            "StandardOutPath": str(
                AMBIENT_ROOT / "logs" / f"{label}.stdout.log"
            ),
            "StandardErrorPath": str(
                AMBIENT_ROOT / "logs" / f"{label}.stderr.log"
            ),
            "EnvironmentVariables": {
                "AMBIENT_OS_ROOT": str(AMBIENT_ROOT),
            },
        }

        if keep_alive:
            plist["KeepAlive"] = {
                "SuccessfulExit": False,
            }

        if watch_paths:
            plist["WatchPaths"] = watch_paths

        return plist

    def _default_sample_script(self, source_name: str) -> str:
        return (
            f"import sys; sys.path.insert(0, '{self._ambient_root}'); "
            f"from telemetry.sampling import SamplingScheduler; "
            f"s = SamplingScheduler(); s.force_sample('{source_name}')"
        )


def _detect_python() -> str:
    """Best-effort detection of the running Python interpreter."""
    import sys
    return sys.executable or "/usr/bin/python3"
