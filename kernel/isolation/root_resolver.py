"""Root resolver — single resolved root per ExecutionContext."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from kernel.isolation.execution_context import ExecutionContext
from kernel.isolation.root_policy import resolve_ambient_root

logger = logging.getLogger("kernel.isolation.root_resolver")


class RootResolver:
    """
    Resolve Ambient OS root once per ExecutionContext.

    All file writes should go through resolve_path() to avoid root ambiguity.
    """

    def __init__(self) -> None:
        self._by_context: dict[str, Path] = {}
        self._global_root: Path | None = None
        self._fallback_logged = False

    def bind_context(self, context: ExecutionContext) -> Path:
        if context.context_id in self._by_context:
            return self._by_context[context.context_id]

        meta_root = context.metadata.get("ambient_root")
        if meta_root:
            root = Path(str(meta_root)).expanduser().resolve()
        else:
            root = self._resolve_once()

        self._by_context[context.context_id] = root
        return root

    def _resolve_once(self) -> Path:
        if self._global_root is None:
            self._global_root = resolve_ambient_root()
            from kernel.isolation.root_policy import _FALLBACK

            if self._global_root == _FALLBACK.resolve() and not self._fallback_logged:
                logger.info("RootResolver using fallback root: %s", self._global_root)
                self._fallback_logged = True
        return self._global_root

    def resolve_path(
        self,
        context: ExecutionContext | None,
        relative: str | Path,
        *,
        must_exist: bool = False,
    ) -> Path:
        if context is not None:
            root = self.bind_context(context)
        else:
            root = self._resolve_once()

        path = (root / Path(relative)).resolve()
        if must_exist and not path.exists():
            raise FileNotFoundError(f"resolved path does not exist: {path}")
        return path

    def write_text(
        self,
        context: ExecutionContext,
        relative: str | Path,
        content: str,
        *,
        encoding: str = "utf-8",
    ) -> Path:
        path = self.resolve_path(context, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return path

    def stats(self) -> dict[str, Any]:
        return {
            "bound_contexts": len(self._by_context),
            "global_root": str(self._global_root) if self._global_root else None,
        }
