"""
Trace Schema — Formal schema definitions for all trace event types.

Provides typed event definitions and validation for the observability layer.
Each subsystem (memory, context, governance, agents, tasks, somatic) defines
a canonical event shape that the tracer, decision log, and system report
can rely on.

Validation ensures trace events conform to their schema before persistence,
preventing corrupt or incomplete observability data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TraceEventType(str, Enum):
    MEMORY_RECALL = "memory_recall"
    CONTEXT_INJECTION = "context_injection"
    GOVERNANCE_CHECK = "governance_check"
    AGENT_EXECUTION = "agent_execution"
    TASK_LIFECYCLE = "task_lifecycle"
    SOMATIC_SIGNAL = "somatic_signal"
    AGENT_DECISION = "agent_decision"
    FAILURE_PROPAGATION = "failure_propagation"


_FIELD_SCHEMAS: dict[str, dict[str, str]] = {
    TraceEventType.MEMORY_RECALL: {
        "query": "str",
        "results_count": "int",
        "total_tokens": "int",
        "dedup_removed": "int",
    },
    TraceEventType.CONTEXT_INJECTION: {
        "agent_id": "str",
        "query": "str",
        "memory_count": "int",
        "tokens_used": "int",
        "compression_applied": "bool",
    },
    TraceEventType.GOVERNANCE_CHECK: {
        "action": "str",
        "agent_id": "str",
        "risk_level": "str",
        "allowed": "bool",
    },
    TraceEventType.AGENT_EXECUTION: {
        "agent_id": "str",
        "task_id": "str",
        "task_name": "str",
        "status": "str",
    },
    TraceEventType.TASK_LIFECYCLE: {
        "task_id": "str",
        "event": "str",
    },
    TraceEventType.SOMATIC_SIGNAL: {
        "signal_type": "str",
        "source": "str",
        "urgency": "int",
    },
    TraceEventType.AGENT_DECISION: {
        "agent_id": "str",
        "task": "str",
        "strategy_chosen": "str",
        "confidence": "float",
    },
    TraceEventType.FAILURE_PROPAGATION: {
        "root_task": "str",
        "skipped_count": "int",
    },
}

_TYPE_VALIDATORS: dict[str, type] = {
    "str": str,
    "int": int,
    "float": (int, float),
    "bool": bool,
    "list": list,
    "dict": dict,
}


@dataclass
class TraceEvent:
    """A validated trace event."""
    event_type: TraceEventType
    attributes: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    trace_id: str = ""
    span_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "attributes": self.attributes,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }


class TraceEventSchema:
    """
    Schema definitions and validation for all trace event types.

    Usage:
        schema = TraceEventSchema()

        valid = schema.validate_event({
            "event_type": "memory_recall",
            "query": "login bug",
            "results_count": 5,
            "total_tokens": 1200,
            "dedup_removed": 1,
        })

        json_schema = schema.to_json_schema()
    """

    def __init__(self):
        self._schemas = dict(_FIELD_SCHEMAS)

    @property
    def event_types(self) -> list[str]:
        """All registered event types."""
        return [t.value for t in TraceEventType]

    def get_schema(self, event_type: str) -> dict[str, str] | None:
        """Get the field schema for an event type."""
        try:
            et = TraceEventType(event_type)
        except ValueError:
            return None
        return self._schemas.get(et)

    def validate_event(self, event: dict[str, Any]) -> bool:
        """
        Validate an event dict against its schema.

        Returns True if the event conforms, False otherwise.
        Required fields must be present and type-correct.
        Extra fields are allowed (open schema).
        """
        event_type_str = event.get("event_type")
        if not event_type_str:
            return False

        try:
            et = TraceEventType(event_type_str)
        except ValueError:
            return False

        schema = self._schemas.get(et)
        if schema is None:
            return False

        for field_name, type_name in schema.items():
            if field_name not in event:
                return False
            expected = _TYPE_VALIDATORS.get(type_name)
            if expected is None:
                continue
            if not isinstance(event[field_name], expected):
                return False

        return True

    def create_event(
        self,
        event_type: str,
        attributes: dict[str, Any],
        trace_id: str = "",
        span_id: str = "",
    ) -> TraceEvent | None:
        """Create a validated TraceEvent, or None if validation fails."""
        check_dict = {"event_type": event_type, **attributes}
        if not self.validate_event(check_dict):
            return None

        return TraceEvent(
            event_type=TraceEventType(event_type),
            attributes=attributes,
            trace_id=trace_id,
            span_id=span_id,
        )

    def to_json_schema(self) -> dict[str, Any]:
        """Export all schemas as a JSON Schema-compatible dict."""
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
        }

        definitions: dict[str, Any] = {}
        for et, fields in self._schemas.items():
            event_name = et.value if isinstance(et, TraceEventType) else et
            properties = {}
            for fname, ftype in fields.items():
                properties[fname] = {"type": type_map.get(ftype, "string")}

            definitions[event_name] = {
                "type": "object",
                "properties": properties,
                "required": list(fields.keys()),
                "additionalProperties": True,
            }

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Ambient OS Trace Event Schema",
            "description": "Schema definitions for all observable trace events",
            "oneOf": [
                {"$ref": f"#/definitions/{name}"}
                for name in definitions
            ],
            "definitions": definitions,
        }
