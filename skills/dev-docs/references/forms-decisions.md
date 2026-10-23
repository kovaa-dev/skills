# Technical and Architectural Decisions

Rules: [requirements](requirements.md) and [work queues](work-queue.md), [documentation rules](documentation.md).
Use the appropriate form; examples are not project decisions. Legacy tasks follow [on-touch conversion](legacy-transition.md).
Adapt paths and field language to the project settings and the checks actually selected.

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

## User approval

Pending. Before accepted, record the exact agreed choice, explicit user confirmation,
approval date and source; if no stable link exists, retain an accurate summary
and date. Document date and validation results do not replace user approval.

## Consequences and constraints

<Confirmed constraints with sources; unresolved assumptions explicitly labeled.>

## Validation

<Research support needed to choose and approve this decision, if any; numeric thresholds
only when justified. Separately state how the implemented contract must be verified;
requirement acceptance belongs in specifications; execution is queued and results belong in artifacts.>
User approval accepts the decision, not its implementation. Do not require a finished
implementation to approve its contract; investigate essential unknowns separately.

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

## User approval

Pending. Before accepted, record the exact agreed choice, explicit user confirmation,
approval date and source; if no stable link exists, retain an accurate summary
and date. Document date and validation results do not replace user approval.

## Contracts and data

<Ownership and cross-layer rules; link other decisions for their own details.>

## Consequences

<Trade-offs and confirmed constraints with sources.>

## Validation

<Research support needed to choose and approve this architecture, if any. Separately state
required verification of the resulting system; execution is queued and verification belongs with the resulting artifact/specification.>
User approval and implementation acceptance are distinct. Do not block approval on
a verification record that can only exist after implementing the approved choice.

## Migration and rollback

<Compatibility, rollout/rollback or explicit not-applicable rationale.>

## Open questions and revisit trigger

<Open questions and conditions for review.>
```

TDs/ADRs do not contain phases, execution checklists, or a second work queue. Decision
dependencies link only to decisions. For `superseded`, specify the reason, date,
applicability boundary, and canonical successor decision. Rejected/withdrawn candidates
retain their disposition and reason; retirement without replacement names its acceptance
source. Do not leave incompatible accepted versions applying to the same scope.

A proposed replacement names its target decision/revision and links to the still-current
choice. Keep the candidate separate and explicitly nonbinding, even if its containing
specification is accepted. Acceptance records the scope and handoff condition before
supersession becomes effective; rejected/withdrawn alternatives retain their reason.
Follow the [proposal lifecycle](requirements.md#proposed-replacements); a proposed TD/ADR
must not silently override an accepted requirement.
