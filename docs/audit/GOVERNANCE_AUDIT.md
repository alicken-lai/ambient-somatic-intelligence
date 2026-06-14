# Governance Consistency Audit

## Boundary Review

| Boundary | Status |
| --- | --- |
| Guardian authority | Preserved. Later kernels explicitly remain advisory. |
| Approval requirements | Preserved. No Phase 8/9 code changes approval rules. |
| Credential policy | Preserved. No identity/reality code edits secrets or credentials. |
| Provider permissions | Preserved. Routing policy remains in orchestration config and CLI flags. |
| Memory write policy | Mostly preserved. DMN append remains external/operator-mediated. |
| External actions | Preserved. External validation is a registry stub only. |

## Kernel-by-Kernel Governance

- Deliberation: advisory reasoning and trace production; Guardian modes represented but not bypassed.
- Routing: enforces provider policy flags and dry-run by default unless invoked.
- Verification/Acquisition/Calibration: produce claims, evidence, confidence, trust, and health scores; no authority to execute actions.
- Reality Alignment: may challenge beliefs and recommend re-verification; cannot override Guardian or provider policy.
- Identity: may describe, classify, and recommend; cannot modify governance, Guardian, provider permissions, or credentials.

## Risks

- Generated reports may be mistaken for policy. README and reports should continue stating advisory-only status.
- Some report commands rebuild lower-level registries. This is not a governance bypass, but it is an auditability concern.

## Recommendation

Keep all governance-changing changes in `hermes/rules/`, `guardian/`, or explicit operator-approved policy commits. Reports should remain evidence, not authority.
