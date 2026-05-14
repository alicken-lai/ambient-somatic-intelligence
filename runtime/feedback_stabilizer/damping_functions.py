from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DampingContext:
    generation: int
    elapsed_seconds: float
    is_engaged: bool
    history: list[float]


@dataclass
class DampedValue:
    original: float
    damped: float
    reduction_pct: float
    strategy: str
    suppressed: bool


class DampingFunctions:

    @staticmethod
    def exponential_decay(value: float, decay_rate: float, elapsed_seconds: float) -> float:
        return value * math.exp(-decay_rate * elapsed_seconds)

    @staticmethod
    def logarithmic_damping(value: float, base: float = 2.0) -> float:
        if value <= 0:
            return 0.0
        return math.log(1 + value, base) / value * value if value != 0 else 0.0

    @staticmethod
    def sigmoid_cap(value: float, midpoint: float = 0.5, steepness: float = 10.0) -> float:
        return 1.0 / (1.0 + math.exp(-steepness * (value - midpoint)))

    @staticmethod
    def hysteresis_gate(
        current: float,
        threshold_engage: float,
        threshold_release: float,
        is_engaged: bool,
    ) -> tuple[float, bool]:
        if is_engaged:
            if current < threshold_release:
                return current, False
            return current, True
        else:
            if current >= threshold_engage:
                return current, True
            return current, False

    @staticmethod
    def moving_average_smooth(values: list[float], window: int = 10) -> float:
        if not values:
            return 0.0
        alpha = 2.0 / (window + 1)
        ema = values[0]
        for v in values[1:]:
            ema = alpha * v + (1 - alpha) * ema
        return ema

    @staticmethod
    def generation_decay(
        base_value: float,
        generation: int,
        decay_per_generation: float = 0.5,
    ) -> float:
        return base_value * (decay_per_generation ** generation)


class DampingPolicy:

    def __init__(self, loop_id: str, strategy: str, params: dict) -> None:
        self.loop_id = loop_id
        self.strategy = strategy
        self.params = params

    def apply(self, value: float, context: DampingContext) -> DampedValue:
        original = value
        suppressed = False

        if self.strategy == "exponential_decay":
            damped = DampingFunctions.exponential_decay(
                value,
                self.params.get("decay_rate", 0.5),
                context.elapsed_seconds,
            )
        elif self.strategy == "logarithmic_damping":
            damped = DampingFunctions.logarithmic_damping(
                value,
                self.params.get("base", 2.0),
            )
        elif self.strategy == "sigmoid_cap":
            damped = DampingFunctions.sigmoid_cap(
                value,
                self.params.get("midpoint", 0.5),
                self.params.get("steepness", 10.0),
            )
        elif self.strategy == "hysteresis_gate":
            damped, _ = DampingFunctions.hysteresis_gate(
                value,
                self.params.get("engage", 0.7),
                self.params.get("release", 0.4),
                context.is_engaged,
            )
        elif self.strategy == "generation_decay":
            damped = DampingFunctions.generation_decay(
                value,
                context.generation,
                self.params.get("decay_per_generation", 0.5),
            )
            if damped < 0.01:
                suppressed = True
        elif self.strategy == "moving_average":
            damped = DampingFunctions.moving_average_smooth(
                context.history + [value],
                self.params.get("window", 10),
            )
        else:
            logger.warning("Unknown damping strategy: %s, passing through", self.strategy)
            damped = value

        reduction = ((original - damped) / original * 100) if original != 0 else 0.0

        return DampedValue(
            original=original,
            damped=damped,
            reduction_pct=reduction,
            strategy=self.strategy,
            suppressed=suppressed,
        )


PRESET_POLICIES: dict[str, DampingPolicy] = {
    "recall_access_boost": DampingPolicy(
        "recall_access_boost", "logarithmic_damping", {"base": 2.0},
    ),
    "rate_tracker_reemit": DampingPolicy(
        "rate_tracker_reemit", "generation_decay", {"decay_per_generation": 0.5},
    ),
    "correlator_reemit": DampingPolicy(
        "correlator_reemit", "generation_decay", {"decay_per_generation": 0.5},
    ),
    "anomaly_actuator": DampingPolicy(
        "anomaly_actuator", "hysteresis_gate", {"engage": 0.7, "release": 0.4},
    ),
    "throttle_death_spiral": DampingPolicy(
        "throttle_death_spiral", "sigmoid_cap", {"midpoint": 0.6, "steepness": 8.0},
    ),
}
