# One-shot migration to requirements and work queues

Use this action only for an explicit request to migrate the selected scope. It replaces
the former task-schema consolidation/hard-renaming workflow. Ordinary selected legacy work
uses [on-touch conversion](legacy-transition.md); both routes produce the same
[requirements](requirements.md) and [queue](work-queue.md) model.

## Scope and recoverability

Agree or infer the exact authorized scope from the request: one capability, a backlog,
or the whole documentation system. Do not turn a local request into a repository-wide
migration. A full migration covers every source type in that scope, regardless of
directory: legacy tasks/PRDs, specifications, decisions, research, findings, checklists,
README/runbooks, indexes, and relevant agent instructions/templates/validators.

Inventory files/headings to locate the selected material, then apply the shared
[coverage and reconciliation protocol](legacy-transition.md#coverage-and-reconciliation)
to every claimed range. Preserve a recoverable immutable revision, patch, or exact copy
before destructive replacement. Use copy/move plus targeted edits where safer; do not
recreate historical sources from memory.

## Perform the transition

1. **Classify and reconcile.** Separate obligations, rationale/decisions, descriptions,
   procedures, questions, work, source facts, navigation, and verification. Resolve [current/proposed/historical state](requirements.md#current-contract-and-nonbinding-material)
   and replacement lineage; preserve candidates as candidates and obsolete text as history,
   not newly accepted obligations. Check applicable accepted contracts for conflicts before
   consolidating; expose both formulations and resolve only the affected choices under
   [decision governance](documentation.md#decision-approval). Use
   [code recovery](requirements.md#recovering-requirements-from-code) for relevant undocumented
   behavior; keep implementation provenance distinct from the legacy baseline and acceptance.
2. **Map meaning to destinations.** Each obligation has one canonical specification/ID;
   each independently useful remaining outcome has one queue entry. Reuse already
   converted records and stable IDs. Several old cards may share a requirement; a card
   may contribute several obligations and results. Do not mechanically turn old task
   IDs/checklist lines into requirements or rename all history. Descriptions and
   procedures retain their own owners under [documentation purpose](documentation.md#documentation-purpose-and-ownership);
   do not convert factual/reference material into invented obligations.
3. **Move content, not dependencies on old docs.** Preserve accepted scope, applicability,
   implementation prerequisites, cross-cutting constraints, questions, rationale,
   technical choices, acceptance sources, and verification. New records are sufficient
   for ordinary execution without old tasks. Historical provenance may link to preserved
   sources but must not be required to understand the current contract.
4. **Build usable queues and history.** Import remaining work with actual readiness,
   priority, accountable owner when known, exact waits, and result/acceptance locators.
   Preserve completed/cancelled outcomes with their actual dates/results/limits.
   Do not label historical work current production verification, reopen done, or lose
   unfinished work inside an archive. Queues may be partitioned with global IDs and
   cross-queue waits; avoid duplicate canonical entries.
5. **Retire converted operational routing.** Apply the
   [range-specific notices](legacy-transition.md#convert-before-continuing) to converted
   source sections and their entrypoints. A shared source's out-of-scope remainder stays
   active and discoverable under on-touch conversion; whole-source retirement requires
   complete coverage. Preserve old links and update affected templates, bootstrap,
   local rules, and parser routing so new work does not regenerate legacy tasks.
6. **Verify the entire agreed scope.** Run the shared two-way coverage check against the
   baseline and [new/changed inputs](requirements.md#questions-during-work). Check graph
   integrity, applicability, proposal targets, retirement redirects, and affected enforcement.
   Name residual/unavailable/unmapped sources and unresolved conflicts. Captured questions
   can remain open; uncovered source meaning prevents a completed full-migration claim.

Progress and a compact source-to-requirement/work/result mapping belong with the migration
work's result. A temporary detailed coverage file is appropriate for a full/large
transition or required audit traceability; do not create a permanent second tracker.
After verification condense working detail under the
[coverage preservation rule](legacy-transition.md#coverage-and-reconciliation), retaining
checkable historical provenance in the result or linked record. Delete sources/coverage
only within granted cleanup authority and after verified recovery.

## Governance and enforcement

When the request also adopts/updates this skill, preserve unique project settings and
scoped exceptions, and use [adoption](adoption.md). Keep one active rule source per
responsibility. Product contracts stay in specifications, work state in queues, and
accepted technical choices in their decision owners; none are copied into the skill.

Update agent instructions, hooks, CI, Git, and delivery automation only under the active
project-work authority. Do not silently disable a validator; adapt its affected schema
and verify migrated samples and remaining legacy readers. Governance-source adoption
and backlog conversion are distinct outcomes; one does not imply the other.

Independent batches may be planned when they have their own outcomes and safe write
boundaries. A joint integration result is work only if it needs independent acceptance.
Migration planning does not authorize launching agents.

## Completion and old action names

The migration is complete only when every source in the declared scope has a verified
destination or an explicit agreed historical/inapplicable disposition, no active legacy
contract or hidden remaining work is left, and ordinary work starts from the new model.
Archived old task documents may remain as history; their continued existence is not
an operational legacy tracker. Do not claim a larger migration than was performed.

A request called "migrate hard", an old task-schema migration, or a consolidation aimed
at adopting this model uses the steps above. Identifier/filename renaming alone does
not satisfy it. Historical ID reassignment is not a default; if specifically requested,
preserve all historical facts, original locators, and incoming resolution separately.
