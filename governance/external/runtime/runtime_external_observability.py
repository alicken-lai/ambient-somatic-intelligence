"""Aggregate runtime external observability for governor attachment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from governance.external.runtime.authority_conflict_guard import AuthorityConflictGuard
from governance.external.runtime.doctrine_runtime_scope import DoctrineRuntimeScope
from governance.external.runtime.export_containment import ExportContainment
from governance.external.runtime.external_runtime_sandbox import ExternalRuntimeSandbox
from governance.external.runtime.runtime_contamination_guard import RuntimeContaminationGuard
from governance.external.runtime.runtime_precedence_guard import RuntimePrecedenceGuard
from governance.external.runtime.runtime_provenance_validator import RuntimeProvenanceValidator


@dataclass
class RuntimeExternalObservability:
    """Read-only runtime soak snapshot — never mutates governance acceptance."""

    advisory_only: bool = True
    sandbox_contained: bool = True
    precedence_safe: bool = True
    sovereignty_safe: bool = True
    ide_boundary_intact: bool = True
    provenance_valid: bool = True
    contamination_clean: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "sandbox_contained": self.sandbox_contained,
            "precedence_safe": self.precedence_safe,
            "sovereignty_safe": self.sovereignty_safe,
            "ide_boundary_intact": self.ide_boundary_intact,
            "provenance_valid": self.provenance_valid,
            "contamination_clean": self.contamination_clean,
            "issues": list(self.issues),
            "disclaimer": "runtime_observational_only",
        }


def observe_runtime_external(
    text: str,
    *,
    scope: str = "advisory",
    is_export: bool = False,
    provenance_record: dict[str, Any] | None = None,
) -> RuntimeExternalObservability:
    sandbox = ExternalRuntimeSandbox()
    scope_guard = DoctrineRuntimeScope()
    precedence = RuntimePrecedenceGuard()
    authority = AuthorityConflictGuard()
    export = ExportContainment()
    provenance = RuntimeProvenanceValidator()
    contam = RuntimeContaminationGuard()

    sb = sandbox.evaluate(text, scope=scope)
    sc = scope_guard.check(text, declared_scope=scope)
    pr = precedence.evaluate(text)
    auth = authority.evaluate(text)
    ex = export.evaluate(text, is_export=is_export)
    pv = provenance.validate(text, record=provenance_record)
    ct = contam.scan(text)

    issues: list[str] = []
    if not sb.contained:
        issues.extend(sb.violations)
    if not sc.in_scope:
        issues.extend(sc.violations)
    if not pr.precedence_safe:
        issues.extend(pr.conflicts)
    if not auth.conflict_free:
        issues.extend(auth.issues)
    if is_export and not ex.contained:
        issues.append("export_not_contained")
    if not pv.valid:
        issues.extend(pv.issues)
    if not ct.clean:
        issues.append("runtime_contamination")

    return RuntimeExternalObservability(
        advisory_only=True,
        sandbox_contained=sb.contained,
        precedence_safe=pr.precedence_safe and auth.precedence_valid,
        sovereignty_safe=auth.sovereignty_safe,
        ide_boundary_intact=ex.boundary_intact,
        provenance_valid=pv.valid,
        contamination_clean=ct.clean,
        issues=issues,
    )
