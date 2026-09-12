# Technical and Architectural Decisions

Rules: [task tracker](task-tracker.md), [documentation rules](documentation.md).
Use the appropriate form; examples and placeholders are not project tasks.
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

<Evidence needed to choose and approve this decision, if any; numeric thresholds
only when justified. Separately state how the implemented contract must be verified;
implementation steps, acceptance and results belong in technical task cards.>
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

<Evidence needed to choose and approve this architecture, if any. Separately state
required verification of the resulting system; execution and results belong in tasks.>
User approval and implementation acceptance are distinct. Do not block approval on
evidence that can only exist after implementing the approved choice.

## Migration and rollback

<Compatibility, rollout/rollback or explicit not-applicable rationale.>

## Open questions and revisit trigger

<Open questions and conditions for review.>
```

TDs/ADRs do not contain phases, task links, or implementation checkboxes. Decision
dependencies link only to decisions. For `superseded`, specify the reason, date, and
canonical successor decision, if one exists; if rejected without a replacement, state
that explicitly. Do not leave two active versions of a contract.
