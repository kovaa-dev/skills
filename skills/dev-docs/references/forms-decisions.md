# Technical and Architectural Decisions

Rules: [requirements](requirements.md) and [work queues](work-queue.md), [documentation rules](documentation.md).
Use the appropriate form; examples are not project decisions. Legacy tasks follow [on-touch conversion](legacy-transition.md).
Adapt paths and field language to the project settings and the checks actually selected.
Use [decision approval](documentation.md#decision-approval) for acceptance authority and
[evidence vocabulary](documentation.md#evidence-vocabulary) to distinguish agreement from
implementation verification. The templates do not add an extra user-approval gate.

## TD — `docs/solutions/auth/TD-AUTH-001.md`

```md
# TD-AUTH-001 Request validation contract

- Status: proposed
- Owner: <contract owner>
- Date: <YYYY-MM-DD>
- Decision dependencies: [ADR-001 Contract ownership](../../architecture/decisions/ADR-001.md)

## Context and boundary

<Problem, owned responsibility and non-goals.>

## Contract and data ownership

<Inputs/outputs, errors, state owner, compatibility and consumer boundaries.>

## Alternatives and decision

<Options, trade-offs and proposed choice.>

## Acceptance source

Pending. <When accepted: exact choice, accepting owner or applied policy/authority,
date and source, including an accurate summary when there is no stable link.>

## Consequences and constraints

<Confirmed constraints with sources; unresolved assumptions explicitly labeled.>

## Validation

<Research support needed to choose this decision, if any; planned implementation checks,
applicable requirement revisions, and actual result/verification locators when available.>

## Migration and rollback

<Procedure or explicit not-applicable rationale.>

## Open questions and revisit trigger

<Remaining open questions and conditions for revisiting the decision.>
```

## ADR — `docs/architecture/decisions/ADR-001.md`

```md
# ADR-001 Contract ownership

- Status: proposed
- Owner: <architecture owner>
- Date: <YYYY-MM-DD>
- Decision dependencies: none

## Context and scope

<Cross-layer problem, responsibility boundaries and non-goals.>

## Alternatives and decision

<Options, proposed choice and rationale.>

## Acceptance source

Pending. <When accepted: exact choice, accepting owner or applied policy/authority,
date and source, including an accurate summary when there is no stable link.>

## Contracts and data

<Ownership and cross-layer rules; link other decisions for their own details.>

## Consequences

<Trade-offs and confirmed constraints with sources.>

## Validation

<Research support needed to choose this architecture, if any; planned system checks,
applicable requirement revisions, and actual result/verification locators when available.>

## Migration and rollback

<Compatibility, rollout/rollback or explicit not-applicable rationale.>

## Open questions and revisit trigger

<Open questions and conditions for review.>
```

TDs/ADRs may explain ordered migration, compatibility, and rollback procedures, or link
the owning runbook, under [documentation purpose](documentation.md#documentation-purpose-and-ownership).
Scheduling, assignees, progress, and completion of particular work belong in the queue.
The Decision dependencies field links decisions; other contract/source links keep their
purpose. For `superseded`, specify the reason, date,
applicability boundary, and canonical successor decision. Rejected/withdrawn candidates
retain their disposition and reason; retirement without replacement names its acceptance
source. Do not leave incompatible accepted versions applying to the same scope.

A proposed replacement names its target decision/revision and links to the still-current
choice. Keep the candidate separate and explicitly nonbinding, even if its containing
specification is accepted. Acceptance records the scope and handoff condition before
supersession becomes effective; rejected/withdrawn alternatives retain their reason.
Follow the [proposal lifecycle](requirements.md#proposed-replacements); a proposed TD/ADR
must not silently override an accepted requirement.
