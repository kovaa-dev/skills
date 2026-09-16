# Product Task

Rules: [task tracker](task-tracker.md), [documentation rules](documentation.md).
Use the appropriate form; examples and placeholders are not project tasks.
Adapt paths and field language to the project settings and the checks actually selected.

## Minimal registration before product grooming

An assigned product hypothesis may be recorded as a short PRD with `backlog` status:
ID, source, hypothesis/problem, owner or `unassigned`, open questions, and a link from
the roadmap. Do not fill in an invented contract, acceptance, or technical scope.
Grooming expands the same card, records evidence, and permits `planned` only after
acceptance; do not create a duplicate merely to change status.

## PRD — `docs/tasks/product/PRD-001.md`

```md
# PRD-001 Sign in to an account

- Status: backlog
- Owner: <product owner>
- Grooming: incomplete
- Source: <requirement source and date>
- Product dependencies: none

## Outcome and scenario

<Actor, problem, desired outcome and end-to-end scenario.>

## User-visible contract

- Surface: <existing interface where the capability lives>.
- Action: <what the user does>.
- Visible result: <what the user sees and can use>.
- Background work: <minimum necessary capability boundary; implementation details stay in technical tasks>.
- Unchanged: <existing UX, workflow, ownership and data boundaries preserved by default>.
- Approval/source: <exact user-confirmed change and date/source; pending while ambiguous>.

## Scope and constraints

<Explicit scope, non-goals and confirmed constraints with sources.>
<Keep unknown choices as open questions; do not invent delivery dates.>

## Technical tasks

- [AUTH-001 Validate sign-in requests](../auth/AUTH-001.md)

## Acceptance

- [ ] PRD-001.1 <Observable end-to-end user outcome and verification method.>
- [ ] PRD-001.2 <Short manual walkthrough of Surface → Action → Visible result.>

## Open questions

<Unresolved product choices, responsible owner and next step.>

## Closure

Pending; for ordinary work record one observable result, consistency with the current
user-visible contract and the end-to-end verification/manual path. If this PRD replaces
an earlier result, confirm the `Replaces` relation. Add date/version/artifacts only when
the tracker requires durable evidence for this risk.
```

When a product slice/phase is needed, its composition is defined here and only through
links to technical cards. Closing technical tasks does not demonstrate end-to-end PRD
acceptance. An undecomposed backlog may not yet have a composition: leave the section
with an explicit open question instead of inventing technical work.

Before `planned`, groom the PRD and replace the metadata with
`- Grooming: completed YYYY-MM-DD; source: <approval>`. When starting a `planned` PRD,
reread its sources, previous outcomes, and prerequisites, give a short execution brief,
and after confirmation set `in-progress`. If new information
changes an accepted product decision before `done`, add a short `## Decision changes`:
the previous and new wording, reason, date, approval source, and affected documents. A
change to the outcome of a `done` PRD gets a new card and
`- Replaces: [PRD-NNN <title>](<path>)`; do not reopen the closed PRD. A cancelled PRD
may be returned to active work while preserving the cancellation reason and the basis
for resuming it.
