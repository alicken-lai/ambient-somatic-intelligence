"""
Somatic Event Layer — Phase 5 of Ambient OS Architecture Refactor.

The core of Ambient Somatic Intelligence: transforms raw environment
signals (CPU, memory, network, disk, processes) into cognitive events
that influence system behavior.

  signal_bus.py          — Pub/sub event bus for somatic signals
  attention_manager.py   — Attention allocation based on signal urgency
  environment_monitor.py — Hardware/OS metric collection and signal emission
  anomaly_event_stream.py — Maps anomaly patterns to cognitive responses
"""

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType
from somatic.attention_manager import AttentionManager, AttentionLevel
from somatic.environment_monitor import EnvironmentMonitor
from somatic.anomaly_event_stream import AnomalyEventStream

__all__ = [
    "SomaticSignalBus",
    "SomaticSignal",
    "SignalType",
    "AttentionManager",
    "AttentionLevel",
    "EnvironmentMonitor",
    "AnomalyEventStream",
]
