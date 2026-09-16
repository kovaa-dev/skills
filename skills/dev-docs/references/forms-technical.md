# Technical task

Rules — [tracker](task-tracker.md), [documentation policy](documentation.md).
Use the applicable form; examples and placeholders are not project tasks.
Adapt paths and field language to the project settings and the checks actually selected.

## Technical task — `docs/tasks/auth/AUTH-001.md`

```md
# AUTH-001 Validate sign-in requests

- Status: backlog
- Owner: <technical owner>
- Grooming: incomplete
- Source: <technical requirement source and date>
- Decisions: [TD-AUTH-001 Request validation contract](../../solutions/auth/TD-AUTH-001.md)
- Dependencies: none
- Parallel with: <optional task links; omit when none>
- Integration: <optional integration-task link; omit when none>

## Result and scope

<Independently verifiable technical result and non-goals.>
Contract details remain in the linked decision, not copied here.

## Open questions

<Unresolved contract questions and required investigation.>
The linked proposal must be accepted before implementing it as a contract.

## Work and acceptance

- [ ] AUTH-001.1 <Implementation step and verifiable acceptance (numeric only when justified).>
- [ ] AUTH-001.2 <Contract/regression checks and expected result.>

## Migration and rollback

<Applicable procedure, or explicit not-applicable rationale.>

## Next step

<Concrete next action.>

## Closure

Pending; for ordinary work, record one observable result, the current canonical source for the
contract/decision when applicable, the closure reconciliation result, and the
verification/manual path. Add environment/date/version/artifacts only for durable evidence required by the
tracker. Explicitly state any mandatory checks not run, unresolved documentation differences, and
remaining limitations.
```

Before `planned`, replace the grooming metadata with
`- Grooming: completed YYYY-MM-DD; source: <approval>`. For `blocked`, add both
`- Blocker: <linked task/artifact/event and reason>` and
`- Unblock condition: <observable result>`; a child relationship is not itself a
blocker. For `need-info`, explicitly record the question, impact, recommendation,
alternatives, and answer owner in the card.

The `Parallel with` and `Integration` fields are conditional; omit them from an ordinary task. Use them
only for an agreed audit/migration task graph; parallel execution means there is no
blocking dependency, not that an agent starts automatically. An integration task must have
its own result and depend on every track it actually integrates.

Record prerequisites in `- Dependencies:` as links to technical tasks.
The source field may link to a specific PRD requirement. One technical task
may be used by `0..N` PRDs; the owning PRD contains the composition, while the backlink registry, stage
codes, and queue are not copied into the technical task. Each task must still appear in
the roadmap exactly once. If shared work has different delivery boundaries or
independent acceptance, split it.

A standalone technical task without a PRD must explain its source, observable result,
impact, and acceptance. It is permitted for migration, dependency/runtime updates, debt/
refactoring, security, reliability/performance, observability/operations, CI/tooling,
investigation, platform capabilities, or removal of an obsolete system. If the work is
needed only for one feature, link it to that feature's PRD; if it changes the user-facing contract, create
or update the PRD. Do not create a fictitious PRD.

If no technical decision (TD) or architecture decision record (ADR) is needed, remove the decisions field; link to an existing contract when
applicable. Keep the research question and verification plan in the task. Do not create
a decision merely to move a task into active work.
