# Source coverage and findings

Rules — [tracker](task-tracker.md), [documentation policy](documentation.md).
Use the applicable form; examples and placeholders are not project tasks.
Adapt paths and field language to the project settings and the checks actually selected.

## Optional: source coverage

A separate `docs/development/source-coverage.md` is a temporary working file only for
a full/large migration, compliance, or explicitly required traceability. A small migration
keeps a compact mapping in the migration task/PR. `Relation to canonical` describes the source's
relationship to the canonical source; `Disposition` records the accepted action. These are not task statuses.

```md
# Source coverage

| Source/version/range | Requirement or question | Canonical destination/new ID | Relation to canonical | Disposition | Rationale / continuation task |
| --- | --- | --- | --- | --- | --- |
| <source and exact range> | <meaning> | <canonical link> | <unique/exact duplicate/semantic duplicate/addition/conflict/historical or not applicable> | <accepted/open/rejected/unmapped> | <reason and task link if unresolved> |

## Checkpoints and remaining scope

- Preserved source: <recoverable version/copy/patch>.
- Current chunk: <explicit boundaries and coverage checks>.
- Not migrated: <source ranges and continuation task links>.
- Completion: <compact closure location; remove this file after approval, or retained evidence policy>.
```

After completion, resolve every `open`/`unmapped` item or list it as
remaining scope. Then consolidate the mapping into the migration task/PR closure and delete the file after
a checkpoint and user approval. Retain the file only as historical evidence when required by
an external audit, compliance, or repository policy; ordinary work does not read or update it.

## Optional: engineering findings

`docs/development/engineering-findings.md` is needed only when a separate
registry has been selected. The form below is used only for a separate registry.
Without one, record a finding that has crossed the registration threshold in an existing or
required technical task: its observation, impact, evidence, and verification conditions use
the task's single status and owner. Do not add a second
Status/Owner, FIND-ID, or Remediation link to the same task. In a separate registry,
the finding status describes the finding, not the progress of its remediation task.

```md
# Engineering findings

## FIND-001 <Short confirmed finding>

- Status: OPEN
- Severity: <project severity level>
- Owner: <one accountable owner>
- Found at: <date/version/environment>
- Code/runtime evidence: <path/lines/reproduction/measurement>
- Impact: <observed impact>
- Remediation: [AUTH-001 Validate sign-in requests](../tasks/auth/AUTH-001.md)
- Expected closure: <verifiable result>
- Closure evidence: pending
```

Allowed finding statuses are `OPEN`, `PARTIAL`, and `CLOSED`. An OPEN or PARTIAL finding requires
a technical task; update the evidence after remediation, and do not
delete closed records. Do not assign a phase to a finding: product composition remains in the PRD.
