"""Provider-neutral action, authorization, result, and trajectory contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
NON_MATERIAL_SIDE_EFFECTS = frozenset({"none", "read_only"})
KNOWN_SIDE_EFFECT_CLASSES = frozenset(
    {"none", "read_only", "local_write", "external_write", "terminal_execution", "mixed_material"}
)
KNOWN_REVERSIBILITY = frozenset({"reversible", "compensatable", "irreversible", "unknown"})
KNOWN_TRAJECTORY_EVENTS = frozenset(
    {
        "proposal_created",
        "authorization_bound",
        "invocation_pending",
        "invocation_completed",
        "invocation_failed",
        "steering_update",
        "tool_pending",
        "tool_completed",
        "tool_cancelled",
    }
)
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,255}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class EnvelopeValidationError(ValueError):
    """Raised when an action or evidence envelope is incomplete or inconsistent."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tuple(values: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class TrajectoryEvent:
    """One uncompressed orchestration/steering event used for replay."""

    event_id: str
    event_type: str
    proposal_id: str
    actor_id: str
    occurred_at: str
    authorization_version: str | None = None
    objective_revision: int = 0
    completed_work: tuple[str, ...] = field(default_factory=tuple)
    pending_tool_calls: tuple[str, ...] = field(default_factory=tuple)
    cancellation_effective: bool | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "completed_work", _tuple(self.completed_work))
        object.__setattr__(self, "pending_tool_calls", _tuple(self.pending_tool_calls))
        object.__setattr__(self, "evidence_refs", _tuple(self.evidence_refs))
        if not self.event_id or not self.proposal_id or not self.actor_id or not self.occurred_at:
            raise EnvelopeValidationError("trajectory event identity, proposal, actor, and timestamp are required")
        if self.event_type not in KNOWN_TRAJECTORY_EVENTS:
            raise EnvelopeValidationError(f"unknown trajectory event type {self.event_type!r}")
        if self.objective_revision < 0:
            raise EnvelopeValidationError("objective_revision must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "proposal_id": self.proposal_id,
            "actor_id": self.actor_id,
            "occurred_at": self.occurred_at,
            "authorization_version": self.authorization_version,
            "objective_revision": self.objective_revision,
            "completed_work": list(self.completed_work),
            "pending_tool_calls": list(self.pending_tool_calls),
            "cancellation_effective": self.cancellation_effective,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ResourceCost:
    """Replayable cost. This is accounting data, not an authorization decision."""

    tokens: int
    time_ms: int
    api_calls: int

    def __post_init__(self) -> None:
        if self.tokens < 0 or self.time_ms < 0 or self.api_calls < 0:
            raise EnvelopeValidationError("resource cost counts must be non-negative")

    def to_dict(self) -> dict[str, int]:
        return {"tokens": self.tokens, "time_ms": self.time_ms, "api_calls": self.api_calls}


@dataclass(frozen=True)
class ActualChange:
    """Observed change descriptor. It does not invent a diff that was not measured."""

    kind: str
    target: str
    summary: str

    def __post_init__(self) -> None:
        if not self.kind.strip() or not self.target.strip() or not self.summary.strip():
            raise EnvelopeValidationError("actual change kind, target, and summary are required")

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "target": self.target, "summary": self.summary}


@dataclass(frozen=True)
class RecordedError:
    category: str
    message: str

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise EnvelopeValidationError("recorded error category is required")

    def to_dict(self) -> dict[str, str]:
        return {"category": self.category, "message": self.message}


def _freeze_arguments(value: Any) -> tuple[tuple[str, str], ...]:
    if not value:
        return ()
    items = value.items() if isinstance(value, dict) else value
    frozen = tuple((str(key), str(item)) for key, item in items)
    if any(not key.strip() for key, _item in frozen):
        raise EnvelopeValidationError("action arguments require names")
    return tuple(sorted(frozen))


@dataclass(frozen=True)
class ProposedActionEnvelope:
    """Complete model proposal; its authorization claim is never trusted alone."""

    proposal_id: str
    intent: str
    requested_scope: tuple[str, ...]
    target: str
    tool: str
    data_class: str
    side_effect_class: str
    reversibility: str
    expected_result: str
    evidence_refs: tuple[str, ...]
    authorization_ref: str | None
    idempotency_key: str
    request_id: str
    trajectory: tuple[TrajectoryEvent, ...] = field(default_factory=tuple)
    schema_version: str = SCHEMA_VERSION
    arguments: tuple[tuple[str, str], ...] | dict[str, Any] = ()
    proposed_by: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_scope", _tuple(self.requested_scope))
        object.__setattr__(self, "evidence_refs", _tuple(self.evidence_refs))
        object.__setattr__(self, "trajectory", tuple(self.trajectory))
        object.__setattr__(self, "arguments", _freeze_arguments(self.arguments))
        if self.proposed_by and not _SAFE_REF.fullmatch(self.proposed_by):
            raise EnvelopeValidationError("proposed_by is not a safe reference")
        required = {
            "proposal_id": self.proposal_id,
            "intent": self.intent,
            "target": self.target,
            "tool": self.tool,
            "data_class": self.data_class,
            "expected_result": self.expected_result,
            "idempotency_key": self.idempotency_key,
            "request_id": self.request_id,
        }
        missing = sorted(key for key, value in required.items() if not str(value).strip())
        if missing or not self.requested_scope:
            raise EnvelopeValidationError(
                "action envelope missing required fields: " + ", ".join([*missing, *( ["requested_scope"] if not self.requested_scope else [])])
            )
        if self.side_effect_class not in KNOWN_SIDE_EFFECT_CLASSES:
            raise EnvelopeValidationError(f"unknown side_effect_class {self.side_effect_class!r}")
        if self.reversibility not in KNOWN_REVERSIBILITY:
            raise EnvelopeValidationError(f"unknown reversibility {self.reversibility!r}")
        if self.authorization_ref is not None and not _SAFE_REF.fullmatch(self.authorization_ref):
            raise EnvelopeValidationError("authorization_ref is not a safe opaque reference")
        if not _SAFE_REF.fullmatch(self.idempotency_key):
            raise EnvelopeValidationError("idempotency_key is not a safe opaque reference")
        if any(event.proposal_id != self.proposal_id for event in self.trajectory):
            raise EnvelopeValidationError("trajectory event proposal_id does not match action envelope")

    @property
    def is_material(self) -> bool:
        return self.side_effect_class not in NON_MATERIAL_SIDE_EFFECTS

    def action_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "request_id": self.request_id,
            "intent": self.intent,
            "requested_scope": list(self.requested_scope),
            "target": self.target,
            "tool": self.tool,
            "data_class": self.data_class,
            "side_effect_class": self.side_effect_class,
            "reversibility": self.reversibility,
            "expected_result": self.expected_result,
            "evidence_refs": list(self.evidence_refs),
            "idempotency_key": self.idempotency_key,
            "arguments": [[key, item] for key, item in self.arguments],
            "proposed_by": self.proposed_by,
            "timestamp": self.timestamp,
        }

    def action_digest(self) -> str:
        return _digest(
            {
                "action": self.action_payload(),
                "trajectory": [event.to_dict() for event in self.trajectory],
            }
        )

    def authorization_scope_digest(self, *, provider_id: str, capabilities: Iterable[str]) -> str:
        return _digest(
            {
                "action": self.action_payload(),
                "trajectory": [event.to_dict() for event in self.trajectory],
                "provider_id": provider_id,
                "capabilities": sorted(str(value) for value in capabilities),
            }
        )

    def with_authorization(self, authorization_ref: str) -> "ProposedActionEnvelope":
        return replace(self, authorization_ref=authorization_ref)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.action_payload(),
            "authorization_ref": self.authorization_ref,
            "trajectory": [event.to_dict() for event in self.trajectory],
        }


@dataclass(frozen=True)
class ExternalAuthorizationBinding:
    """Authorization supplied by a trusted checker outside model output."""

    authorization_ref: str
    authorization_version: str
    issuer_id: str
    scope_digest_sha256: str
    decision: str = "ALLOW"

    def __post_init__(self) -> None:
        if not _SAFE_REF.fullmatch(self.authorization_ref):
            raise EnvelopeValidationError("external authorization_ref is missing or unsafe")
        if not _SAFE_REF.fullmatch(self.authorization_version) or not _SAFE_REF.fullmatch(self.issuer_id):
            raise EnvelopeValidationError("authorization version and issuer must be safe opaque references")
        if not _SHA256.fullmatch(self.scope_digest_sha256):
            raise EnvelopeValidationError("authorization scope digest must be sha256")
        if self.decision != "ALLOW":
            raise EnvelopeValidationError("only an external ALLOW can bind a material action")

    def bind(
        self,
        proposal: ProposedActionEnvelope,
        *,
        provider_id: str,
        capabilities: Iterable[str],
    ) -> ProposedActionEnvelope:
        expected = proposal.authorization_scope_digest(provider_id=provider_id, capabilities=capabilities)
        if self.scope_digest_sha256 != expected:
            raise EnvelopeValidationError("external authorization scope does not match proposed action")
        if proposal.authorization_ref not in {None, self.authorization_ref}:
            raise EnvelopeValidationError("model-supplied authorization_ref does not match external authorization")
        return proposal.with_authorization(self.authorization_ref)


@dataclass(frozen=True)
class ResultEvidenceEnvelope:
    """Normalized, replayable evidence for one provider invocation result."""

    result_id: str
    proposal_id: str
    request_id: str
    provider: str
    model: str | None
    status: str
    idempotency_key: str
    action_digest_sha256: str
    output_digest_sha256: str
    authorization_ref: str | None
    authorization_version: str | None
    started_at: str
    completed_at: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trajectory: tuple[TrajectoryEvent, ...] = field(default_factory=tuple)
    pending_tool_calls: tuple[str, ...] = field(default_factory=tuple)
    cancelled_tool_calls: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = SCHEMA_VERSION
    actual_changes: tuple[ActualChange, ...] = ()
    recorded_error: RecordedError | None = None
    cost: ResourceCost | None = None
    replay_pointer: str = ""
    verified_by: str | None = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_refs", _tuple(self.evidence_refs))
        object.__setattr__(self, "trajectory", tuple(self.trajectory))
        object.__setattr__(self, "pending_tool_calls", _tuple(self.pending_tool_calls))
        object.__setattr__(self, "cancelled_tool_calls", _tuple(self.cancelled_tool_calls))
        object.__setattr__(self, "actual_changes", tuple(self.actual_changes))
        if not self.timestamp:
            object.__setattr__(self, "timestamp", self.completed_at)
        if not self.result_id or not self.proposal_id or not self.request_id:
            raise EnvelopeValidationError("result/proposal/request identity is required")
        if not _SHA256.fullmatch(self.action_digest_sha256) or not _SHA256.fullmatch(self.output_digest_sha256):
            raise EnvelopeValidationError("result evidence digests must be sha256")
        if self.authorization_ref is not None and not _SAFE_REF.fullmatch(self.authorization_ref):
            raise EnvelopeValidationError("result authorization_ref is unsafe")
        if self.verified_by is not None and (
            not _SAFE_REF.fullmatch(self.verified_by) or self.verified_by in {"cursor-agent", "implementer"}
        ):
            raise EnvelopeValidationError("verified_by must be an independent verifier reference")
        if self.replay_pointer and not (
            _SHA256.fullmatch(self.replay_pointer) or _SAFE_REF.fullmatch(self.replay_pointer)
        ):
            raise EnvelopeValidationError("replay_pointer is not a safe reference")

    @property
    def action_ref(self) -> str:
        return self.proposal_id

    @property
    def outcome(self) -> str:
        if self.status in {"success", "fallback", "idempotent_replay"}:
            return "success"
        if self.status == "timeout":
            return "timeout"
        if self.status == "partial":
            return "partial"
        return "failure"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "result_id": self.result_id,
            "proposal_id": self.proposal_id,
            "request_id": self.request_id,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "action_digest_sha256": self.action_digest_sha256,
            "output_digest_sha256": self.output_digest_sha256,
            "authorization_ref": self.authorization_ref,
            "authorization_version": self.authorization_version,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "evidence_refs": list(self.evidence_refs),
            "trajectory": [event.to_dict() for event in self.trajectory],
            "pending_tool_calls": list(self.pending_tool_calls),
            "cancelled_tool_calls": list(self.cancelled_tool_calls),
            "action_ref": self.action_ref,
            "outcome": self.outcome,
            "actual_changes": [change.to_dict() for change in self.actual_changes],
            "error": None if self.recorded_error is None else self.recorded_error.to_dict(),
            "cost": None if self.cost is None else self.cost.to_dict(),
            "replay_pointer": self.replay_pointer,
            "verified_by": self.verified_by,
            "timestamp": self.timestamp,
        }


def output_digest(content: str, status: str) -> str:
    return _digest({"content": content, "status": status})
