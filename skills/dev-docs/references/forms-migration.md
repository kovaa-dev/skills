# Migration coverage

Rules — [migration](governance-migration.md), [documentation policy](documentation.md).
Use this form only for a full/large migration, compliance, or explicitly required
traceability. A small migration keeps a compact mapping in its migration task or PR.
Adapt paths and field language to the project settings.

`docs/development/migration-coverage.md` is a temporary control file, not a task,
roadmap, research artifact, or verification record. `Relation to canonical` describes
the source's relationship to the destination; `Disposition` records the accepted action.

```md
# Migration coverage

| Source/version/range | Requirement or question | Canonical destination/new ID | Relation to canonical | Disposition | Rationale / continuation task |
| --- | --- | --- | --- | --- | --- |
| <source and exact range> | <meaning> | <canonical link> | <unique/exact duplicate/semantic duplicate/addition/conflict/historical or not applicable> | <accepted/open/rejected/unmapped> | <reason and task link if unresolved> |

## Checkpoints and remaining scope

- Preserved source: <recoverable version/copy/patch>.
- Current chunk: <explicit boundaries and coverage checks>.
- Not migrated: <source ranges and continuation task links>.
- Completion: <compact closure location; remove this file after approval, or state the required retention policy>.
```

At completion, resolve every `open` or `unmapped` item or list it as remaining scope.
Consolidate the result into the migration task/PR closure and delete the temporary file
after a checkpoint and user approval. Retain it only when an external audit, compliance,
repository policy, or explicit traceability decision requires a historical migration record;
ordinary work does not read or update it.
