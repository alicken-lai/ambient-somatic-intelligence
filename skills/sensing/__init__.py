"""
skills.sensing — Sensing and detection skills.

Exports:
  - thermal_anomaly_detect_skill: Detect thermal anomalies from telemetry
"""

from __future__ import annotations

from skills.sensing.thermal_anomaly_detect import thermal_anomaly_detect_skill

__all__ = [
    "thermal_anomaly_detect_skill",
]
