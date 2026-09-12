# Bootstrap for a portable documentation system

The canonical rules are the [documentation governance](documentation.md) and
[task tracker rules](task-tracker.md). This guide describes adoption;
the [forms](documentation-registers-template.md) provide starter cards, not a second
set of rules. Historical `*.history.md` files are not part of the package.

After adoption, use the [product discovery process](product-discovery.md):
for a new product, it establishes the nearest minimum outcome and sequence;
for an existing product, it determines the actual state and future feature delivery without
retrospectively renaming history. Micro-grooming is performed before implementation of each PRD;
empty templates do not replace it.

## Adopting the rules

The user chooses one of two methods under the [adoption workflow](adoption.md): a complete
copy of `dev-docs` in the repository or a pinned link to the public skill. No separate mode/
profile is stored; the method is visible from the project-local directory or entrypoint. In either
case, the project stores product documentation, tasks, decisions, settings, and evidence. Existing
rules and accepted migration changes remain in effect until adoption is verified.

## Init without product grooming

Create a minimal documentation index and task entrypoint, and agree on placement,
language, and access to the skill. The layer register may be empty; do not require a completed architecture,
requirements, or code. Cards and decision indexes appear as real work requires them.
Init does not select the product/stack and does not authorize a bulk migration. If existing
rules require consolidation, agree on migrate rather than overwriting them.

Prepare adoption and perform the normal affected-scope check. A full check
is required only by explicit request or repository/org/compliance policy. On failure,
retain the previous working source and identify the remainder in the migration task/PR.

## Agent entrypoint adoption contract

`dev-docs` creates docs/task settings and specifies the required entrypoint. Changes to
AGENTS/RULES are made only under the active project-work policy; if it does not grant
explicit authority, obtain separate permission to edit the entrypoint.
Add the entrypoint only after selecting the adoption method and creating settings:

```md
## Documentation governance

For work on requirements, tasks, decisions and documentation, load the complete
project-local skill at [.agents/skills/dev-docs](.agents/skills/dev-docs), or the
public dev-docs source pinned below. Read only the relevant references, then apply
[project documentation settings](docs/development/documentation-index.md) and approved
scoped exceptions.

Published source: <public Git URL at immutable commit SHA, or omit for project-local copy>.
If the configured source is incomplete or unavailable, report the blocker; do not
invent rules or silently substitute another copy.
```

Do not restate general rules here. Every required contributor, not only the current agent,
must have access to the skill. Automatic loading is provided by environment/project
instructions, but does not guarantee error-free execution; CI requires
separate executable checks, as Markdown does not run by itself.

## Explicit settings for a new project

Record one `Project settings` section in the documentation index. The forms file
provides the section format. Approve:

- scoped exceptions and, only for a published source, a public pinned link;
- paths for cards, decisions, history, and navigation;
- the selected roadmap sequence and how to display completed tasks; for a new
  product, propose but do not impose `Alpha/Beta/RC/Release/Next`;
- the register of actual layers already known: prefix and responsibility; add a decision index
  when the layer has decisions;
- prose language and the format of metadata fields/statuses;
- applicable constraints and their acceptance sources;
- selected docs/parser checks and a temporary source mapping location only for a full/
  large migration or required traceability;
- reading routes for working questions and document boundaries under the governance section
  “Granularity of any document”;
- the method for preserving documentation history, including immutable Git links.

Git/PR, release/changelog, commit/version, and response-language rules belong to the
project-work policy; docs settings may only link to its canonical source.

`AUTH` (authentication) and `WEB` (web interface) are exclusively English
instructional examples. Do not create these layers, services, teams, or tasks if they
are not needed by the project. Do not infer a product, platforms, budgets,
performance/security/compliance constraints, or solution readiness from templates.
An unknown gets an explicit question and a known accountable owner or an explicit
`unassigned`; do not invent an owner.

Choose the language and metadata according to project settings. If a constrained
parser is connected, check the [compatibility profile](validator-compatibility.md)
rather than imposing its constraints on a project without such a tool.

## Minimal initial structure

Expand the initial structure as content appears (it is not a mandatory
set of empty files for init):

```text
 docs/development/documentation-index.md
 docs/tasks/index.md                 # selected roadmap, all tasks, and status projection
 docs/tasks/product/                 # PRD-NNN.md as requirements appear
 docs/tasks/<layer>/                 # <LAYER>-NNN.md
 docs/solutions/index.md             # links to layer decision indexes
 docs/solutions/<layer>/index.md     # TDs, not tasks/phases
 docs/architecture/decisions/index.md # ADRs
```

The space before `docs/` above is only visual indentation. Create layer directories
from the actual register. If a validator is selected, create only the structure it
actually requires after checking the tool's requirements. Do not generate hundreds of empty
tasks, mandatory marketing registers, or a second delivery plan.
An explicitly assigned product hypothesis that requires tracking may be registered as a minimal
backlog PRD before grooming; fill in the product contract and acceptance after sufficient
grooming, and perform micro-grooming before implementation. Create a technical task for
independently planned/tracked work; a local fix/refactor within an existing
contract does not automatically receive a card. Every created task is immediately visible in the
roadmap. Add a TD/ADR only for an actual decision; a backlog item without a decision contains
open questions.

## Bootstrap / small migration

When transitioning an existing project, first perform
[consolidation of scattered rules](governance-migration.md). Searching for
rules, matching duplicates, resolving conflicts, and moving content into canonical sources are mandatory.
The following steps do not replace this reconciliation with simple template copying.

1. Read existing instructions, requirements, and affected code; distinguish
   implemented state from proposals. Select settings explicitly.
2. Create minimal indexes from the forms; add only existing
   goals as links. Preserve the source of every requirement.
3. Register with stable PRD/technical IDs only assigned work, accepted
   deferred work, and unresolved independently actionable/high-risk work that meets the tracker's
   threshold, without inventing delivery/release dates, phases, or decisions. Preserve the date
   of a known source; define delivery contents only in the PRD.
4. When moving legacy material, select a small scope; preserve a checkpoint
   and original bodies through copy/move before rewriting. Keep compact old→new mapping in the
   migration task/PR; a separate temporary file is needed only for a full/large migration
   or policy-required traceability.
5. Move the selected section, update inbound links, and retain one current
   version. Mark history explicitly; do not rewrite closed acceptance/evidence.
   List the remainder with sources and continuation tasks.
6. Check links, unique IDs, the dependency graph, acceptance/evidence,
   a single owner/status, visibility of all cards in the roadmap, and the absence of a second
   plan. An independent
   review is possible but does not require a particular tool or model.

After the move, perform the [adoption check](adoption.md). An intermediate batch or
partial-project audit does not mean that migration is complete.

## Adoption checks

Check links, the absence of conflicting rules, and readability through working-question routes.
For created cards, check unique IDs, dependency types,
acceptance, and absence of duplication. Use existing project checks;
when none exist, perform a manual check and state its limits.
Validators are useful for recurring mechanical errors, but are not required for agent work
and do not prove requirement completeness or decision acceptance. Introducing a new
validator is separate accepted work justified by error volume and recurrence.
Do not create tooling automatically during every init.
Optional technical details are covered by [compatibility](validator-compatibility.md).
