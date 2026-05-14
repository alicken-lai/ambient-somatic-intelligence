from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AmplificationConfig:
    max_generation_depth: int = 4
    max_global_rate: float = 100.0
    max_per_type_rate: float = 30.0
    rate_window_seconds: float = 60.0
    cascade_detection_window: float = 10.0
    max_cascade_signals: int = 10


@dataclass
class AmplificationCheckResult:
    allowed: bool
    signal_type: str
    generation: int
    current_rate: float
    reason: str
    damped_value: float | None


class AmplificationController:

    def __init__(self, config: AmplificationConfig | None = None) -> None:
        self._config = config or AmplificationConfig()
        self._emissions: dict[str, deque[float]] = {}
        self._global_emissions: deque[float] = deque()
        self._cascade_window: deque[tuple[float, int]] = deque()

    def check_amplification(
        self,
        signal_type: str,
        generation: int,
        source: str,
    ) -> AmplificationCheckResult:
        now = time.time()
        self._prune_windows(now)

        if generation > self._config.max_generation_depth:
            return AmplificationCheckResult(
                allowed=False,
                signal_type=signal_type,
                generation=generation,
                current_rate=self._get_type_rate(signal_type, now),
                reason=f"Generation {generation} exceeds max depth {self._config.max_generation_depth}",
                damped_value=None,
            )

        global_rate = self._get_global_rate(now)
        if global_rate >= self._config.max_global_rate:
            return AmplificationCheckResult(
                allowed=False,
                signal_type=signal_type,
                generation=generation,
                current_rate=global_rate,
                reason=f"Global emission rate {global_rate:.1f}/min exceeds limit {self._config.max_global_rate}",
                damped_value=None,
            )

        type_rate = self._get_type_rate(signal_type, now)
        if type_rate >= self._config.max_per_type_rate:
            return AmplificationCheckResult(
                allowed=False,
                signal_type=signal_type,
                generation=generation,
                current_rate=type_rate,
                reason=f"Per-type rate {type_rate:.1f}/min exceeds limit {self._config.max_per_type_rate}",
                damped_value=None,
            )

        if self._is_cascade(now) and generation > 2:
            return AmplificationCheckResult(
                allowed=False,
                signal_type=signal_type,
                generation=generation,
                current_rate=type_rate,
                reason=f"Cascade active, suppressing generation-{generation} signal",
                damped_value=None,
            )

        return AmplificationCheckResult(
            allowed=True,
            signal_type=signal_type,
            generation=generation,
            current_rate=type_rate,
            reason="Within limits",
            damped_value=None,
        )

    def record_emission(self, signal_type: str, source: str, generation: int) -> None:
        now = time.time()
        if signal_type not in self._emissions:
            self._emissions[signal_type] = deque()
        self._emissions[signal_type].append(now)
        self._global_emissions.append(now)
        self._cascade_window.append((now, generation))

    def _prune_windows(self, now: float) -> None:
        cutoff = now - self._config.rate_window_seconds
        for sig_type in list(self._emissions.keys()):
            q = self._emissions[sig_type]
            while q and q[0] < cutoff:
                q.popleft()
            if not q:
                del self._emissions[sig_type]

        while self._global_emissions and self._global_emissions[0] < cutoff:
            self._global_emissions.popleft()

        cascade_cutoff = now - self._config.cascade_detection_window
        while self._cascade_window and self._cascade_window[0][0] < cascade_cutoff:
            self._cascade_window.popleft()

    def _get_global_rate(self, now: float) -> float:
        self._prune_windows(now)
        return float(len(self._global_emissions))

    def _get_type_rate(self, signal_type: str, now: float) -> float:
        q = self._emissions.get(signal_type)
        if q is None:
            return 0.0
        return float(len(q))

    def _is_cascade(self, now: float) -> bool:
        return len(self._cascade_window) >= self._config.max_cascade_signals

    def get_current_amplification(self) -> float:
        now = time.time()
        self._prune_windows(now)
        total = float(len(self._global_emissions))
        if total <= 1:
            return 1.0
        derived = sum(
            1 for _, gen in self._cascade_window if gen > 0
        )
        if derived == 0:
            return 1.0
        root = total - derived
        if root <= 0:
            return total
        return total / max(root, 1.0)

    def get_emission_rates(self) -> dict[str, float]:
        now = time.time()
        self._prune_windows(now)
        return {
            sig_type: float(len(q))
            for sig_type, q in self._emissions.items()
        }

    def is_cascade_active(self) -> bool:
        now = time.time()
        self._prune_windows(now)
        return self._is_cascade(now)

    def reset(self) -> None:
        self._emissions.clear()
        self._global_emissions.clear()
        self._cascade_window.clear()
