"""Area 3 — Root resolution hardening."""

from __future__ import annotations

from pathlib import Path

from kernel.isolation.execution_context import ExecutionContext, Permission
from kernel.isolation.execution_scope import ScopeType
from kernel.isolation.root_policy import resolve_ambient_root
from kernel.isolation.root_resolver import RootResolver


def test_resolve_ambient_root_is_directory() -> None:
    root = resolve_ambient_root()
    assert root.is_dir()


def test_root_bound_per_context(governed_context: ExecutionContext) -> None:
    resolver = RootResolver()
    p1 = resolver.bind_context(governed_context)
    p2 = resolver.bind_context(governed_context)
    assert p1 == p2


def test_resolve_path_under_root(governed_context: ExecutionContext) -> None:
    resolver = RootResolver()
    path = resolver.resolve_path(governed_context, "kernel/__init__.py", must_exist=True)
    assert path.name == "__init__.py"
    assert Path("kernel") in path.parents or path.parent.name == "kernel"
