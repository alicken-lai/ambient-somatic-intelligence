"""Consistent pressure → dimension normalization for v0.4 observability gates."""

from __future__ import annotations

from kernel.entropy.entropy_metric import MetricKind
from kernel.entropy.entropy_controller import EntropyReport


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def dimension_from_pressure(pressure: float) -> float:
    """Map normalized pressure (0=healthy) to stability dimension (1=healthy)."""
    return clamp01(1.0 - clamp01(pressure))


def metric_value(report: EntropyReport, name: str, default: float = 0.0) -> float:
    for metric in report.snapshot.metrics:
        if metric.name == name:
            return metric.value
    return default


def pressure_max(
    report: EntropyReport,
    *names: str,
    default: float = 0.0,
) -> float:
    """Worst-case pressure across named metrics (avoids dilution via averaging)."""
    if not names:
        return default
    return max((metric_value(report, n, default) for n in names), default=default)


def kind_pressure_max(
    report: EntropyReport,
    kind: MetricKind,
    *,
    prefer_names: tuple[str, ...] = (),
) -> float:
    """
    Max pressure for a metric kind.

    When prefer_names is set, only those metrics are considered (gate-aligned subset).
    """
    if prefer_names:
        return pressure_max(report, *prefer_names)
    values = [m.value for m in report.snapshot.by_kind(kind)]
    return max(values) if values else 0.0
