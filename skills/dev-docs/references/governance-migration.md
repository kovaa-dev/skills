# One-shot migration to requirements and work queues

Use this action only for an explicit request to migrate the selected scope. Ordinary
work uses [source assessment and incremental transition](source-transition.md); both
routes produce the same requirements, queues, and documentation ownership model.
Preserve sources that already fit it; migration is semantic reconciliation, not uniform
filenames, directories, or compulsory rewriting.

## Scope and recoverability

Agree or infer the exact authorized scope from the request: one capability, a backlog,
or the whole documentation system. Do not turn a local request into a repository-wide
migration. A full migration covers every source type in that scope, regardless of
directory: work records, specifications, decisions, research, findings, checklists,
README/runbooks, indexes, and relevant agent instructions/templates/validators.

Inventory files/headings to locate the selected material, then apply the shared
[coverage and reconciliation protocol](source-transition.md#coverage-and-reconciliation)
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
   behavior; keep implementation provenance distinct from the source baseline and acceptance.
2. **Map meaning to destinations.** Each obligation has one canonical specification/ID;
   each independently useful selected outcome has a separate task and queue entry. Reuse already
   converted records and stable IDs. Several old cards may share a requirement; a card
   may contribute several obligations and results. Separate knowledge from execution
   under [task conversion](source-transition.md#convert-before-continuing); preserve
   compatible task IDs, status, result boundaries, and history. Reuse prior extraction
   mappings and owners instead of migrating the same knowledge again. Do not mechanically turn old task
   IDs/checklist lines into requirements or rename all history. Descriptions and
   procedures retain their own owners under [documentation purpose](documentation.md#documentation-purpose-and-ownership);
   do not convert factual/reference material into invented obligations.
3. **Move content, not dependencies on old docs.** Preserve accepted scope, applicability,
   implementation prerequisites, cross-cutting constraints, questions, rationale,
   technical choices, acceptance sources, and verification. New records are sufficient
   for ordinary execution without superseded source text. Historical provenance may link to preserved
   sources but must not be required to understand the current contract.
4. **Build usable queues and history.** Reuse the existing queue/index and update its
   entries in place under [queue continuity](work-queue.md#existing-queues-during-transition).
   Import remaining work with actual readiness,
   priority, accountable owner when known, exact waits, and result/acceptance locators.
   Keep task bodies minimal; context is owned by requirements, decisions, defects,
   research, and results. Every actual remaining execution outcome stays selectable,
   including the unfinished part of a mixed historical card.
   Preserve completed/cancelled outcomes with their actual dates/results/limits.
   Do not label historical work current production verification, reopen done, or lose
   unfinished work inside an archive. Queues may be partitioned with global IDs and
   cross-queue waits; avoid duplicate canonical entries.
5. **Verify before switching.** Perform the [verification cycle](#verification-cycle)
   against the entire agreed baseline and
   [new/changed inputs](requirements.md#questions-during-work).
   Name residual/unavailable/unmapped sources and unresolved conflicts. Captured questions
   can remain open; uncovered source meaning prevents a completed full-migration claim
   and keeps the affected source ranges active.
6. **Switch verified routing and check the result.** Apply the
   [range-specific notices](source-transition.md#convert-before-continuing) to converted
   source sections and their entrypoints. A shared source's out-of-scope remainder stays
   active and discoverable under on-touch conversion; whole-source retirement requires
   complete coverage. Preserve old links and update affected templates, bootstrap,
   local rules, and parser routing so they lead to target owners without duplicating contracts.
   After switching, check graph integrity, applicability, proposal targets, retirement
   redirects, and affected enforcement. Reconcile material source/input changes since
   the coverage check, then complete the final full pass of the verification cycle
   before claiming completion.

Progress and a compact source-to-requirement/work/result mapping belong with the migration
work's result. A temporary detailed coverage file is appropriate for a full/large
transition or required audit traceability; do not create a permanent second tracker.
After verification condense working detail under the
[coverage preservation rule](source-transition.md#coverage-and-reconciliation), retaining
checkable historical provenance in the result or linked record. Delete sources/coverage
only within granted cleanup authority and after verified recovery.

## Verification cycle

Run this cycle proactively for the entire declared migration scope; do not wait for
separate requests to check omissions, conflicts, excess, or implementation alignment.
A first transfer or a passing link/ID validator is not sufficient. Reuse the shared
[semantic coverage protocol](source-transition.md#coverage-and-reconciliation) rather
than creating a second accounting system.

Every full pass covers these directions:

- **Sources to destinations and back:** account for every source unit, including
  conditions, exceptions, dependencies, unfinished outcomes, and evidence; reject
  invented scope, weakened obligations, or unsupported acceptance/verification claims.
- **Contracts against one another:** compare sources with sources and current owners
  with current owners, including cross-cutting constraints. Distinguish applicability,
  accepted replacements, proposals, and history before declaring a conflict.
- **Requirements against implementation and evidence, in both directions:** for the
  migrated functionality, inspect relevant code and tests/artifacts to find mismatches,
  unsupported completion claims, and material behavior without a documented basis.
  Record code-derived observations with provenance; implementation is not acceptance.
  Missing planned functionality is not itself a regression. Historical completion is
  not fresh runtime verification. Use appropriate available checks and state static,
  runtime, and unverified boundaries; do not expand this into an unrelated code audit.
- **Ownership, economy, and work visibility:** detect duplicate contracts, administrative
  migration prose, mixed obligations/results, hidden remaining work, and status drift
  between owners and queue projections. Consolidation must preserve all meaning and
  evidence, not merely shorten files.
- **Independent usability:** follow the new entrypoints to select work and understand
  its contract without superseded source text. Check links, IDs, prerequisites, proposal
  targets, redirects, templates, and relevant enforcement, including after route changes.
  Historical provenance links are not execution dependencies.

For each finding, correct migration errors within the authorized scope and recheck
both the correction and its affected dependencies/consumers. Capture product defects
and unresolved decisions at their canonical owners, with independently actionable work
registered under the queue rules. Do not silently change product policy or repair
production code merely to make migration checks pass. Capturing a conflict preserves
coverage but does not make the affected work ready.

After corrections stabilize, perform a full control pass across all directions above
against the final candidate and any inputs changed since the baseline. If that pass
finds another migration error, correct it, recheck the impact, and repeat the full pass.
Stop successfully only when the final full pass finds no new migration errors, all
in-scope meaning is accounted for, material defects/discrepancies are fixed and verified within current work or linked
to independently selectable remediation tasks, and
the new reading/work routes are usable. Product bugs and captured open questions may
remain; their implementation or resolution is not a prerequisite for migration closure.

Do not repeat identical blocked checks indefinitely or substitute confidence for
coverage. If a necessary source, environment, or user decision prevents verification,
finish independent checks, name the exact unchecked range and blocker, and report
partial/limited completion instead of certifying the entire migration. Explain why a
check is inapplicable where relevant; an unavailable check is not a passed check.

Keep compact pass coverage, findings, corrections, and remaining limits in the existing
migration result/report, with the retained source mapping. Do not create permanent
scripts, another queue, or migration history inside requirements solely for this loop.

## Governance and enforcement

When the request also adopts/updates this skill, preserve unique project settings and
scoped exceptions, and use [adoption](adoption.md). Keep one active rule source per
responsibility. Product contracts stay in specifications, execution status in tasks with explicit queue projections, and
accepted technical choices in their decision owners; none are copied into the skill.

Update agent instructions, hooks, CI, Git, and delivery automation only under the active
project-work authority. Do not silently disable a validator; adapt its affected schema
and verify migrated samples and remaining source readers. Governance-source adoption
and backlog conversion are distinct outcomes; one does not imply the other.

Independent batches may be planned when they have their own outcomes and safe write
boundaries. A joint integration result is work only if it needs independent acceptance.
Migration planning does not authorize launching agents.

## Completion

The migration is complete only when every source in the declared scope has a verified
destination or an explicit agreed historical/inapplicable disposition, no unmapped active
contract or hidden remaining work is left, ordinary work starts from the new model,
and the final full [verification pass](#verification-cycle) satisfies its closure criteria.
Preserved sources may remain as history with an explicit route to their current owners.
Do not claim a larger migration than was performed.
