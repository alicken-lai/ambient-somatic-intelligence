"""Single reversible patch handle with restore()."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class PatchHandle:
    """Records one applied patch and can restore the original binding."""

    patch_id: str
    phase: str
    target: Any
    attr_name: str
    original: Any
    replacement: Any
    timestamp: float = field(default_factory=time.time)
    restored: bool = field(default=False, repr=False)
    callback_remover: Callable[[], None] | None = field(default=None, repr=False)

    @property
    def is_active(self) -> bool:
        return not self.restored

    def restore(self) -> bool:
        """Restore original method or remove callback. Returns True if restored."""
        if self.restored:
            return False
        if self.callback_remover is not None:
            self.callback_remover()
        else:
            setattr(self.target, self.attr_name, self.original)
        self.restored = True
        return True
