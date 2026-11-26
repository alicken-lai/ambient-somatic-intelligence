# Memory Layer Policy

## Purpose

ASI memory is structured, auditable experience. This policy defines memory layers, promotion expectations, retention expectations, deletion constraints, and audit requirements.

## Memory Layers

### Short-Term Memory

Short-term memory is immediate session context. It supports local reasoning and task continuity but is not automatically governed memory.

Short-term memory may be discarded unless promoted through an explicit memory path.

### Working Memory

Working memory is active operational context used to complete a task. It may include current files, recent decisions, temporary assumptions, and open risks.

Working memory must not become durable memory unless the record has a clear purpose and source.

### DMN Memory

DMN memory is append-only durable project memory. It records important project history, operator preferences, unresolved ambiguity, prior incidents, governance decisions, and repeated topics.

DMN records must be written in English to avoid encoding corruption and mixed-script recall noise.

### Replay Memory

Replay memory preserves evidence needed to reconstruct decisions. It should answer what happened, why it happened, what evidence existed, what memory was recalled, and which governance rule applied.

Replay memory must preserve uncertainty and failed checks.

### Governance Memory

Governance memory stores constitutional rules, review outcomes, safety decisions, doctrine changes, and policy decisions.

Governance memory must be conservative, traceable, and aligned with repository artifacts.

## Memory Promotion Rules

Promote memory only when it is:

- Relevant beyond the current turn.
- Useful for future safety, governance, or project continuity.
- Supported by a clear source.
- Written with confidence and uncertainty preserved.
- Compatible with append-only memory doctrine.

Do not promote:

- Raw chat history without structure.
- Speculation presented as fact.
- Strategy without earned validation.
- Sensitive data without a governed reason.
- Vector recall results as truth.

## Memory Retention Rules

Retain records that support:

- Governance history.
- Auditability.
- Replay reconstruction.
- Incident analysis.
- Operator preferences.
- Project architecture decisions.
- Known risks and unresolved ambiguity.

Retention should prefer summaries, references, and metadata over raw sensitive content.

## Memory Deletion Rules

Memory is append-only by default. Historical records, failed gates, incident entries, and gap records must not be silently deleted to improve scores or presentation.

Deletion or repair requires a governed process that records:

- The original issue.
- The reason repair is required.
- The reviewer or approval path.
- The replacement or correction record.
- The replay impact.

When deletion is legally, ethically, or operationally required, preserve an audit-safe tombstone or repair record unless prohibited by higher policy.

## Memory Audit Requirements

Memory-affecting changes must document:

- Source.
- Timestamp or time range.
- Confidence.
- Promotion reason.
- Replay pointer when available.
- Governance state.
- Sensitive data impact.
- Whether the record is raw, summarized, inferred, or verified.

Memory audits must check for:

- Unsupported promotion.
- Hidden failures.
- Encoding corruption.
- Over-retention of sensitive data.
- Missing replay references.
- Conflation of recall evidence with truth.
