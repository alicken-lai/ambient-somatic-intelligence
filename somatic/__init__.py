"""
Somatic Event Layer — Ambient OS environmental cognition subsystem.

Transforms raw environment signals (CPU, memory, network, disk, processes)
into cognitive events that influence system behavior.

  signal_bus.py            — Pub/sub event bus for somatic signals
  attention_manager.py     — Attention allocation based on signal urgency
  environment_monitor.py   — Hardware/OS metric collection and signal emission
  anomaly_event_stream.py  — Maps anomaly patterns to cognitive responses
  signal_normalizer.py     — Adaptive baseline normalization (Phase 7)
  signal_correlator.py     — Compound pattern detection (Phase 7)
  rate_tracker.py          — Event rate monitoring and spike detection (Phase 7)
  signal_analytics.py      — Analytical queries over signal history (Phase 7)
"""

from somatic.signal_bus import SomaticSignalBus, SomaticSignal, SignalType
from somatic.attention_manager import AttentionManager, AttentionLevel
from somatic.environment_monitor import EnvironmentMonitor
from somatic.anomaly_event_stream import AnomalyEventStream
from somatic.signal_normalizer import SignalNormalizer, NormalizedSignal
from somatic.signal_correlator import SignalCorrelator, CorrelatedEvent
from somatic.rate_tracker import RateTracker
from somatic.signal_analytics import SignalAnalytics

__all__ = [
    "SomaticSignalBus",
    "SomaticSignal",
    "SignalType",
    "AttentionManager",
    "AttentionLevel",
    "EnvironmentMonitor",
    "AnomalyEventStream",
    "SignalNormalizer",
    "NormalizedSignal",
    "SignalCorrelator",
    "CorrelatedEvent",
    "RateTracker",
    "SignalAnalytics",
]
