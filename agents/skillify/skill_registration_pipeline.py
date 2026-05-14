"""
Skill Registration Pipeline — Governance-gated skill registration.

Manages the full lifecycle: propose → governance review → approve/reject → register.
All candidate skills require explicit governance approval before registration.
Registration is always reversible via rollback.

Storage: agents/skillify/pipeline_state.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.skillify.skill_candidate_generator import SkillCandidate
from agents.skillify.skill_candidate_validator import (
    CandidateValidation,
    SkillCandidateValidator,
)

logger = logging.getLogger(__name__)

AMBIENT_ROOT = Path(os.environ.get("AMBIENT_OS_ROOT", Path.home() / "ambient-os"))
PIPELINE_STATE_PATH = AMBIENT_ROOT / "agents" / "skillify" / "pipeline_state.jsonl"
PENDING_REGISTRATIONS_PATH = AMBIENT_ROOT / "agents" / "skillify" / "pending_registrations.jsonl"


@dataclass
class ProposalResult:
    """Result of proposing a candidate for governance review."""
    proposal_id: str
    status: str
    governance_ticket: str
    candidate_id: str
    validation: CandidateValidation | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "governance_ticket": self.governance_ticket,
            "candidate_id": self.candidate_id,
        }
        if self.validation:
            result["validation"] = self.validation.to_dict()
        return result


@dataclass
class ApprovalResult:
    """Result of approving a proposal."""
    proposal_id: str
    status: str
    approved_by: str
    approved_at: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "notes": self.notes,
        }


@dataclass
class RegistrationResult:
    """Result of registering an approved skill."""
    skill_id: str
    registered_at: str
    reversible: bool
    registry_used: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "registered_at": self.registered_at,
            "reversible": self.reversible,
            "registry_used": self.registry_used,
        }


@dataclass
class _PipelineEntry:
    """Internal state for a pipeline proposal."""
    proposal_id: str
    candidate: SkillCandidate
    status: str  # pending_review, approved, rejected, registered, rolled_back
    governance_ticket: str
    validation: CandidateValidation | None = None
    approved_by: str | None = None
    approved_at: str | None = None
    approval_notes: str = ""
    skill_id: str | None = None
    registered_at: str | None = None
    rejected_reason: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "candidate": self.candidate.to_dict(),
            "status": self.status,
            "governance_ticket": self.governance_ticket,
            "validation": self.validation.to_dict() if self.validation else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "approval_notes": self.approval_notes,
            "skill_id": self.skill_id,
            "registered_at": self.registered_at,
            "rejected_reason": self.rejected_reason,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> _PipelineEntry:
        candidate = SkillCandidate.from_dict(data.get("candidate", {}))

        val_data = data.get("validation")
        validation = None
        if val_data and isinstance(val_data, dict):
            validation = CandidateValidation(
                is_valid=val_data.get("is_valid", False),
                errors=val_data.get("errors", []),
                warnings=val_data.get("warnings", []),
                quality_score=val_data.get("quality_score", 0.0),
                recommendations=val_data.get("recommendations", []),
            )

        return _PipelineEntry(
            proposal_id=data.get("proposal_id", ""),
            candidate=candidate,
            status=data.get("status", "pending_review"),
            governance_ticket=data.get("governance_ticket", ""),
            validation=validation,
            approved_by=data.get("approved_by"),
            approved_at=data.get("approved_at"),
            approval_notes=data.get("approval_notes", ""),
            skill_id=data.get("skill_id"),
            registered_at=data.get("registered_at"),
            rejected_reason=data.get("rejected_reason"),
            created_at=data.get("created_at", ""),
        )


class SkillRegistrationPipeline:
    """
    Governance-gated skill registration pipeline.

    Full lifecycle: propose → validate → governance review → approve → register.
    Skills are NEVER auto-approved or auto-deployed.

    Usage:
        pipeline = SkillRegistrationPipeline()
        result = pipeline.propose(candidate)
        pipeline.approve(result.proposal_id, reviewer="admin", notes="LGTM")
        reg = pipeline.register(result.proposal_id)
    """

    def __init__(
        self,
        state_path: Path | str | None = None,
        validator: SkillCandidateValidator | None = None,
    ):
        self._state_path = Path(state_path) if state_path else PIPELINE_STATE_PATH
        self._validator = validator or SkillCandidateValidator()
        self._entries: dict[str, _PipelineEntry] = {}
        self._load()

    def propose(self, candidate: SkillCandidate) -> ProposalResult:
        """
        Propose a candidate for governance review.

        Validates the candidate first. If validation fails, the proposal
        is still created but marked as rejected.
        """
        validation = self._validator.validate(candidate)

        proposal_id = f"prop-{uuid.uuid4().hex[:8]}"
        governance_ticket = f"GOV-{uuid.uuid4().hex[:6].upper()}"

        if not validation.is_valid:
            status = "rejected"
            candidate.status = "rejected"
            logger.warning(
                "Candidate '%s' failed validation: %s",
                candidate.proposed_name, validation.errors,
            )
        else:
            status = "pending_review"
            candidate.status = "proposed"

        entry = _PipelineEntry(
            proposal_id=proposal_id,
            candidate=candidate,
            status=status,
            governance_ticket=governance_ticket,
            validation=validation,
            rejected_reason="; ".join(validation.errors) if not validation.is_valid else None,
        )

        self._entries[proposal_id] = entry
        self._persist()

        self._record_governance_audit(
            action=f"skill_proposal:{candidate.proposed_name}",
            proposal_id=proposal_id,
            status=status,
        )

        logger.info(
            "Proposed candidate '%s' → proposal %s (status=%s, ticket=%s)",
            candidate.proposed_name, proposal_id, status, governance_ticket,
        )

        return ProposalResult(
            proposal_id=proposal_id,
            status=status,
            governance_ticket=governance_ticket,
            candidate_id=candidate.candidate_id,
            validation=validation,
        )

    def approve(self, proposal_id: str, reviewer: str, notes: str = "") -> ApprovalResult:
        """Approve a pending proposal. Only works on pending_review proposals."""
        entry = self._entries.get(proposal_id)
        if entry is None:
            raise ValueError(f"Proposal '{proposal_id}' not found")
        if entry.status != "pending_review":
            raise ValueError(
                f"Cannot approve proposal in state '{entry.status}' "
                f"(must be 'pending_review')"
            )

        now = datetime.now(timezone.utc).isoformat()
        entry.status = "approved"
        entry.approved_by = reviewer
        entry.approved_at = now
        entry.approval_notes = notes
        entry.candidate.status = "approved"
        entry.candidate.reviewed_at = datetime.now(timezone.utc)
        entry.candidate.reviewer_notes.append(f"[{reviewer}] {notes}")

        self._persist()
        self._record_governance_audit(
            action=f"skill_approval:{entry.candidate.proposed_name}",
            proposal_id=proposal_id,
            status="approved",
            reviewer=reviewer,
        )

        logger.info("Approved proposal %s by %s", proposal_id, reviewer)

        return ApprovalResult(
            proposal_id=proposal_id,
            status="approved",
            approved_by=reviewer,
            approved_at=now,
            notes=notes,
        )

    def register(self, proposal_id: str) -> RegistrationResult:
        """
        Register an approved skill.

        Interfaces with SkillRegistry if available, otherwise stores
        in pending_registrations.jsonl.
        """
        entry = self._entries.get(proposal_id)
        if entry is None:
            raise ValueError(f"Proposal '{proposal_id}' not found")
        if entry.status != "approved":
            raise ValueError(
                f"Cannot register proposal in state '{entry.status}' "
                f"(must be 'approved')"
            )

        skill_id = f"skill-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        registry_used = "pending_registrations"

        registered_via_registry = self._try_skill_registry(entry.candidate, skill_id)
        if registered_via_registry:
            registry_used = "skill_registry"

        if not registered_via_registry:
            self._store_pending_registration(entry.candidate, skill_id, now)

        entry.status = "registered"
        entry.skill_id = skill_id
        entry.registered_at = now
        entry.candidate.status = "registered"

        self._persist()
        self._record_governance_audit(
            action=f"skill_registration:{entry.candidate.proposed_name}",
            proposal_id=proposal_id,
            status="registered",
            skill_id=skill_id,
        )

        logger.info(
            "Registered skill '%s' (id=%s) via %s",
            entry.candidate.proposed_name, skill_id, registry_used,
        )

        return RegistrationResult(
            skill_id=skill_id,
            registered_at=now,
            reversible=True,
            registry_used=registry_used,
        )

    def reject(self, proposal_id: str, reason: str) -> None:
        """Reject a pending proposal."""
        entry = self._entries.get(proposal_id)
        if entry is None:
            raise ValueError(f"Proposal '{proposal_id}' not found")
        if entry.status not in ("pending_review", "approved"):
            raise ValueError(f"Cannot reject proposal in state '{entry.status}'")

        entry.status = "rejected"
        entry.rejected_reason = reason
        entry.candidate.status = "rejected"

        self._persist()
        self._record_governance_audit(
            action=f"skill_rejection:{entry.candidate.proposed_name}",
            proposal_id=proposal_id,
            status="rejected",
        )

        logger.info("Rejected proposal %s: %s", proposal_id, reason)

    def rollback(self, skill_id: str) -> bool:
        """Deregister a previously registered skill. Returns True if successful."""
        target: _PipelineEntry | None = None
        for entry in self._entries.values():
            if entry.skill_id == skill_id and entry.status == "registered":
                target = entry
                break

        if target is None:
            logger.warning("No registered skill found with id '%s'", skill_id)
            return False

        rolled_back = self._try_skill_registry_deregister(skill_id)
        if not rolled_back:
            self._remove_pending_registration(skill_id)

        target.status = "rolled_back"
        target.candidate.status = "draft"

        self._persist()
        self._record_governance_audit(
            action=f"skill_rollback:{target.candidate.proposed_name}",
            proposal_id=target.proposal_id,
            status="rolled_back",
            skill_id=skill_id,
        )

        logger.info("Rolled back skill '%s'", skill_id)
        return True

    def list_pending(self) -> list[dict[str, Any]]:
        """List all pending proposals."""
        return [
            entry.to_dict() for entry in self._entries.values()
            if entry.status == "pending_review"
        ]

    def list_registered(self) -> list[dict[str, Any]]:
        """List all skills registered through this pipeline."""
        return [
            entry.to_dict() for entry in self._entries.values()
            if entry.status == "registered"
        ]

    def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        """Get details for a specific proposal."""
        entry = self._entries.get(proposal_id)
        return entry.to_dict() if entry else None

    # --- Internal helpers ---

    def _try_skill_registry(self, candidate: SkillCandidate, skill_id: str) -> bool:
        """Attempt to register via SkillRegistry if the skills layer is available."""
        try:
            from skills.core.skill_registry import SkillRegistry
            from skills.core.skill_schema import SkillSchema

            schema = SkillSchema(
                name=candidate.proposed_name,
                version=candidate.proposed_version,
                inputs=[
                    {"name": inp["name"], "type": inp.get("type", "Any")}
                    for inp in candidate.proposed_inputs
                ],
                outputs=[
                    {"name": out["name"], "type": out.get("type", "Any")}
                    for out in candidate.proposed_outputs
                ],
                confidence_range=candidate.confidence_range,
                routing_conditions=candidate.routing_conditions,
                memory_updates=candidate.memory_updates,
                governance_level=candidate.governance_level,
                observability_hooks=candidate.observability_hooks,
                execute=lambda inputs: {"status": "placeholder", "skill_id": skill_id},
            )

            registry = SkillRegistry()
            registry.register(schema)
            logger.info("Registered via SkillRegistry: %s", candidate.proposed_name)
            return True
        except ImportError:
            logger.debug("SkillRegistry not available — using fallback storage")
            return False
        except Exception as e:
            logger.warning("SkillRegistry registration failed: %s", e)
            return False

    def _try_skill_registry_deregister(self, skill_id: str) -> bool:
        """Attempt to deregister via SkillRegistry if available."""
        try:
            from skills.core.skill_registry import SkillRegistry
            registry = SkillRegistry()
            if hasattr(registry, "deregister"):
                registry.deregister(skill_id)
                return True
            return False
        except (ImportError, Exception):
            return False

    def _store_pending_registration(
        self,
        candidate: SkillCandidate,
        skill_id: str,
        registered_at: str,
    ) -> None:
        """Store in pending_registrations.jsonl as fallback."""
        path = PENDING_REGISTRATIONS_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "skill_id": skill_id,
            "candidate": candidate.to_dict(),
            "registered_at": registered_at,
            "status": "active",
        }
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to store pending registration: %s", e)

    def _remove_pending_registration(self, skill_id: str) -> None:
        """Mark a pending registration as rolled back."""
        path = PENDING_REGISTRATIONS_PATH
        if not path.exists():
            return

        records: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("skill_id") == skill_id:
                            rec["status"] = "rolled_back"
                        records.append(rec)
                    except json.JSONDecodeError:
                        continue

            with path.open("w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to update pending registration: %s", e)

    def _record_governance_audit(self, **kwargs: Any) -> None:
        """Record an audit entry via GovernanceAuditLog if available."""
        try:
            from governance.audit_log import GovernanceAuditLog
            from governance.policy_engine import RiskLevel

            audit = GovernanceAuditLog()
            status = kwargs.get("status", "unknown")
            risk = RiskLevel.REVIEW_REQUIRED if status == "pending_review" else RiskLevel.ALLOW
            if status == "rejected":
                risk = RiskLevel.BLOCK

            audit.record_decision(
                action=kwargs.get("action", "skillify_pipeline"),
                risk=risk,
                reason=f"Skillify pipeline: {status}",
                agent_id="skillify",
                matched_policies=["skillify_governance"],
                metadata={
                    "proposal_id": kwargs.get("proposal_id"),
                    "skill_id": kwargs.get("skill_id"),
                    "reviewer": kwargs.get("reviewer"),
                    "pipeline_status": status,
                },
            )
        except (ImportError, Exception) as e:
            logger.debug("Governance audit not available: %s", e)

    def _persist(self) -> None:
        """Persist all pipeline state to JSONL."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._state_path.open("w", encoding="utf-8") as f:
                for entry in self._entries.values():
                    f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to persist pipeline state: %s", e)

    def _load(self) -> None:
        """Load pipeline state from JSONL."""
        if not self._state_path.exists():
            return
        try:
            with self._state_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = _PipelineEntry.from_dict(data)
                        self._entries[entry.proposal_id] = entry
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug("Skipping malformed pipeline entry: %s", e)
        except OSError as e:
            logger.warning("Failed to load pipeline state: %s", e)
