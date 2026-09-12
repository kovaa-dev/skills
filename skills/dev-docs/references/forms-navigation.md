# Navigation and Settings

Rules: [task tracker](task-tracker.md), [documentation rules](documentation.md).
Use the appropriate form; examples and placeholders are not project tasks.
Adapt paths and field language to the project settings and the checks actually selected.

The project README and instructions link directly to the task index specified in the
settings (`docs/tasks/index.md` by default); do not create an additional root redirect
file.

## Task index — `docs/tasks/index.md`

```md
# Task index

## Alpha

### Product

| Task | Status |
| --- | --- |
| [PRD-001 Sign in to an account](product/PRD-001.md) | `planned` |

### AUTH

| Task | Status |
| --- | --- |
| [AUTH-001 Validate sign-in requests](auth/AUTH-001.md) | `backlog` |

## Beta

## RC

## Release

## Next

## History
```

This is the standard example for a new product, not a mandatory structure. During
product grooming, the user may rename, combine, extend, or replace delivery groups.
For an existing product, first determine the actual current state and future sequence
without labeling old history with invented stages. Within a group, use Product and
actual technical layer subgroups when needed.

The index is the only roadmap and shows every registered task exactly once. An active
task belongs to one delivery group; `done`/`cancelled` remains in the last assigned
group or moves to `History`. `History` is not a stage and does not prove delivery. The
index contains only the selected group, internal order, links, and compact status
projection. Use the `Task | Status` table and the same lowercase token as the card by
default; the settings may select another unambiguous format. Do not add owner,
acceptance, prerequisites, blocker/progress, or a second milestone registry. Update the
status and projection in the same batch; strikethrough does not replace the token. The
`Replaces` relation appears only in the new PRD. Before selecting a sequence, a heading
is sufficient for an empty project; after selection, create the agreed empty groups
without sample links.

## Decision indexes

`docs/solutions/index.md`:

```md
# Technical decisions

- [AUTH decisions](auth/index.md)
```

`docs/solutions/auth/index.md`:

```md
# AUTH decisions

- [TD-AUTH-001 Request validation contract](TD-AUTH-001.md)
```

`docs/architecture/decisions/index.md`:

```md
# Architecture decisions

- [ADR-001 Contract ownership](ADR-001.md)
```

## Navigation and settings — `docs/development/documentation-index.md`

```md
# Documentation index

## Project settings

- Published rule source: <public Git URL at immutable commit SHA/content digest; omit when the full skill is copied into .agents/skills/dev-docs>.
- Approved scoped exceptions: <links or none>.
- Prose language: English.
- Tracker schema: English baseline profile.
- Task paths: docs/tasks/product and docs/tasks/<layer>; filename: <ID>.md.
- Decision paths: docs/solutions/<layer> and docs/architecture/decisions.
- Task status tokens: backlog, planned, in-progress, blocked, done, cancelled.
- Roadmap sequence: <chosen groups; for a new product default Alpha, Beta, RC, Release, Next>.
- Historical task placement: <keep in last assigned delivery group, or move once to History>.
- Task-index status projection: `Task | Status`; every registered task appears once and matches its canonical card.
- Decision status tokens: proposed, accepted, superseded.
- Metadata: one “- Status:” and one “- Owner:” per canonical card.
- Documentation history path: <chosen path; clearly marked *.history.md; not active governance>.
- Findings: <task cards, or chosen register path>.
- Temporary source mapping: <location only for an active full/large migration or policy-required traceability, otherwise none>.
- Code map: <chosen location when code structure is stable>.
- Documentation checks: <explicitly selected docs/parser checks and compatible runtime, or manual review>.
- Constraints: <links to accepted project sources; unknowns remain open questions>.

## Layer registry

| Prefix | Responsibility | Decision index, when present |
| --- | --- | --- |
| AUTH | Authentication contract (example only) | docs/solutions/auth/index.md |
| WEB | Web interface (example only) | docs/solutions/web/index.md |

## Read by question

- What work exists? [Task index](../tasks/index.md).
- What technical contracts apply? [Technical decisions](../solutions/index.md).
- What cross-layer rules apply? [Architecture decisions](../architecture/decisions/index.md).
```

Replace the example registry with actual layers; do not create WEB automatically. The
registry defines the layer namespace/responsibility; it does not duplicate the owner of
individual cards or contract text. Before the first decision, the decision index may be
set to `none` or omitted according to the project format. Add navigation links only to
documents that exist.
