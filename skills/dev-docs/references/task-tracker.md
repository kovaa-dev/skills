# Legacy task tracker recognition

**Legacy only.** The current model is [requirements/specifications](requirements.md)
plus [lean work queues](work-queue.md). Before continuing work on any old PRD/task,
perform [on-touch conversion](legacy-transition.md). This file identifies old records;
it does not authorize new legacy cards or continued task-based execution.

## Recognize and preserve old meaning

| Legacy material | Destination/handling |
| --- | --- |
| PRD-NNN outcome, behavior, constraints, acceptance | Canonical specification requirements and acceptance scenarios. |
| Layer task scope, steps, prerequisites | Remaining result-oriented queue work; place useful detail under [work-context ownership](documentation.md#work-context-and-results). |
| Bug/deferred fix | Queue work linked to the violated requirement; no duplicate requirement for unchanged behavior. |
| Investigation | Queue work plus its question, method, and result artifact. |
| TD/ADR | Existing decision remains canonical when applicable; capture separately addressable obligations without duplicating the choice. |
| Done/cancelled cards and closure | Historical queue results with original sources, dates, and verification limits. |
| Task index/roadmap | New queue entrypoint plus explicit links to remaining legacy work; replace active status copies with canonical entries/links. |
| Open questions, findings, exceptions | Owning specification/decision/artifact, with queue work only when independently actionable. |

Legacy IDs such as PRD-NNN, WEB-NNN, and AUTH-NNN identify source records, not new
requirement IDs. Preserve their history and incoming resolution. Neither a layer prefix
nor membership in a product task proves an implementation dependency.

Old lifecycle tokens may include backlog, planned, in-progress, need-info, blocked, done,
and cancelled. Preserve the original facts. An old planned status without sufficient
accepted scope/inputs is not proof of readiness; a done parent is not proof that every
extracted obligation is currently verified. Use the new queue semantics after conversion.

## Compatibility boundary

Keep only the minimum reader/alias required to enter unconverted records. Old schema
checks can remain scoped to still-legacy records while the project parser is adapted.
Do not force a converted specification/queue entry back into a PRD or layer-task template
to satisfy an obsolete validator. Follow [validator compatibility](validator-compatibility.md).

The former whole-backlog task-schema migration and hard renaming instructions are
replaced by [one-shot migration](governance-migration.md). Normal conversion preserves
stable source IDs/history; a rename alone is not migration to the new model.
