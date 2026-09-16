# Incoming Bugs, Findings, and Ideas

Rules: [task tracker](task-tracker.md), [documentation rules](documentation.md).
Use the appropriate form; examples and placeholders are not project tasks.
Adapt paths and field language to the project settings and the checks actually selected.

## Short intake forms

This is a minimal registration, not an implementation-ready specification. See the
[maintenance rules](maintenance.md) for triage, severity, and planning rules. Replace
example IDs with available IDs from actual layers. Grooming before `planned` assigns
an owner, accepts the nearest task's verifiable outcome, dependencies, and priority,
and records evidence. For an
investigation, the outcome may be an answer to a specific question rather than a
finished product solution. Full design is unnecessary for registration. If an
applicable contract exists, link to it; a TD/ADR is needed only for a genuine technical
choice.

### Bug

```md
# WEB-001 <Observed defect>

- Status: backlog
- Type: bug
- Owner: unassigned
- Grooming: incomplete
- Source: <report/source and date>
- Dependencies: none
- Severity: <critical/high/medium/low/unknown + impact evidence>
- Priority: <project priority or pending triage + rationale>

## Reproduction

<Version/environment, prerequisites, steps, expected and actual behavior.>
<Frequency, affected users, workaround; omit personal data and secrets.>

## Open questions

<What remains unconfirmed; distinguish cause hypothesis from observed behavior.>

## Scheduling decision and next step

<Queue placement rationale, or explicit deferral reason and review trigger.>
<Next action and responsible triage owner. Queue itself contains only task links.>

## Acceptance

- [ ] WEB-001.1 Original reproduction no longer fails.
- [ ] WEB-001.2 Regression/validation result follows the active project-work policy;
      record the chosen check and any explicit blocker/exception without copying that policy.

## Evidence

Pending; record actual checks and any manual-only validation limitation.
```

### Technical finding or debt

```md
# WEB-002 <Observation to investigate>

- Status: backlog
- Type: investigation
- Owner: unassigned
- Grooming: incomplete
- Source: <review/measurement/report and date>
- Dependencies: none

## Observation and impact

<Observed evidence, affected boundary and known impact.>
<Hypothesis, separately labeled; for known maintenance work use type maintenance.>

## Open questions

<What needs checking and how to confirm or reject the hypothesis.>

## Next step

<Next check and triage owner; priority and decision before planned.>

## Acceptance

- [ ] WEB-002.1 Investigation conclusion has reproducible evidence.
- [ ] WEB-002.2 Remaining fixes have linked open tasks, or no action is justified.

## Evidence

Pending; investigation completion does not mean remediation completion.
```

### Product idea

```md
# PRD-001 <Potential user outcome>

- Status: backlog
- Type: idea
- Owner: unassigned
- Grooming: incomplete
- Source: <request/interview and date>
- Product dependencies: none

## Problem and potential value

<Who has the problem, context, desired benefit; hypothesis, not accepted scope.>

## Open questions and next step

<What to learn, how to test value, responsible triage owner.>

## Technical tasks

Not decomposed; technical scope follows validation of the product choice.
```

This minimal backlog PRD may be registered before product grooming; it is not an
accepted product contract. Grooming refines the same card into a feature/improvement
with verifiable acceptance and evidence, after which selected work may become
`planned`; do not create a duplicate merely because its type changes. A product phase is optional, but the roadmap
must link to the task.
