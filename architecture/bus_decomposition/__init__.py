"""IntegrationBus decomposition safety review — analysis and infrastructure.

Provides typed event schemas, connection lifecycle tracking, risk analysis,
and a prioritized refactor plan for the IntegrationBus subsystem.
"""

from architecture.bus_decomposition.bus_risk_report import (
    BusRiskReport,
    BusRiskReportGenerator,
    RiskFinding,
)
from architecture.bus_decomposition.connection_registry import (
    ConnectionRecord,
    ConnectionRegistry,
    RegistryHealthReport,
)
from architecture.bus_decomposition.event_schema import (
    BusEventSchema,
    EventField,
    EventSchemaRegistry,
    EventValidationResult,
)
from architecture.bus_decomposition.refactor_plan import (
    EffortEstimate,
    RefactorPlan,
    RefactorPlanGenerator,
    RefactorStep,
)

__all__ = [
    "BusEventSchema",
    "BusRiskReport",
    "BusRiskReportGenerator",
    "ConnectionRecord",
    "ConnectionRegistry",
    "EffortEstimate",
    "EventField",
    "EventSchemaRegistry",
    "EventValidationResult",
    "RefactorPlan",
    "RefactorPlanGenerator",
    "RefactorStep",
    "RegistryHealthReport",
    "RiskFinding",
]
