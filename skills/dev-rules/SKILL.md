---
name: dev-rules
description: >-
  A unified standard for executing engineering tasks in projects: scope boundaries,
  worktree/branch safety, product-visible-first implementation, minimal complexity,
  tests and E2E without unnecessary harnesses, checks, subagents, Git, draft/ready PRs,
  and handoff. Use before changing code, configuration, CI, Git history, or delivery
  state, and when applying init, audit, migrate, or update actions to project-work rules.
---

# dev-rules


## Responsibility

This skill defines **how to perform** engineering work. Requirements, the PRD, task
tracker, TD/ADR, decision-making, and documentation history belong in the project's
canonical product and documentation sources. Do not copy their governance rules here
or create documents solely to satisfy this skill.

The method for adopting project-work rules is defined by the
[adoption workflow](references/adoption.md): either a complete copy of the skill in the
repository or an explicit pinned reference to the published skill. An unnamed semantic
duplicate is a migration defect, while a project-specific rule is valid only as a
setting or an explicitly accepted scoped exception. This skill does not grant authority
for destructive operations, merge, release, or deploy.

## Lifecycle and automatic application

Actions:

- **apply** — perform a routine engineering task under the rules below;
- **init** — adopt the skill as an automatically loaded project-work source;
- **audit** — read-only review of local rules and automation, with conflicts discussed;
- **migrate** — after approval, remove or replace conflicts and semantic duplicates
  while preserving project settings and scoped exceptions;
- **update** — for a new revision, perform a limited audit + migrate, including removal
  of older local requirements when the revision relaxes or removes them.

For `init`, `audit`, `migrate`, and `update`, follow the
[adoption workflow](references/adoption.md). Installing the skill does not activate it
by itself. After explicit selection and verification, a project-local copy or pinned
project instruction automatically loads the skill for routine code/config/CI/Git/delivery
tasks; the user does not need to invoke it manually. No separate governance mode or
profile is stored.

## 1. Start and correct worktree

Before the first write:

1. Determine the exact requested result and mode: read-only, implementation, or
   Git/delivery.
2. Check the active editor/code-navigation project (Serena, when available), the shell
   Git top-level/worktree, branch, and status.
3. Derive the intended branch from the request, active PR/task, or explicit project
   setting. The active tool root, shell worktree, and edited paths must match.
4. If they do not match, reactivate the correct project/worktree or stop; do not write
   to an accidentally opened checkout.
5. Run the project bootstrap/route/resume command if one exists, and read only the rules
   it names and their immediate owner sources.

When a task needs a separate workspace, first use the current environment's workspace
management (for example its UI, API, or CLI) if available. Reuse a suitable workspace
for the same task. Switch the active workspace when the environment supports it;
otherwise explicitly target its directory. Before writing, verify that the tool root,
shell cwd, Git worktree, branch, and edited paths refer to the intended workspace.
If the environment cannot manage workspaces, use a Git worktree at the project-defined
location, or `<repo>/.worktrees/<task-slug>` with a local ignore when none is defined.
Do not create worktrees under an arbitrary `/tmp` or another ad hoc location.

Run bootstrap/shared-state commands (`agent:*`, install, prepare, codegen, migrations,
Git config, and similar commands) sequentially. Run commands in parallel only when they
are proven read-only and have no shared workspace/cache/Git side effects.

Do not perform a network fetch before local analysis. Fetch/integration is needed only
before creating a branch from a remote base, when explicitly requested, before ready/merge,
or when there is a known conflict or contract-compatibility risk.

## 2. Source of truth and confirmed scope

Read the project's applicable canonical product/documentation sources and do not
reinterpret their product meaning. A separate documentation skill is not required: use
the project PRD/tasks and accepted TD/ADR when they exist, then treat the user's latest
explicit decision and shipped behavior as the preservation default. If sources are
missing or conflict, ask; do not declare the code an accepted invariant or invent your
own contract.

When work uses a tracker with the `dev-docs` lifecycle, implementation may start from
an entire PRD or a technical task. `backlog` first undergoes grooming and acceptance;
`need-info` waits for an answer, and `blocked` waits for its stated unblock condition.
For `planned`, do not repeat grooming: provide a short execution brief covering what
will be done, the observable result, what remains unchanged, checks, and the manual
path, then obtain explicit confirmation to start. The initial request may already
confirm that same brief. After confirmation, update the selected PRD/task and its index
projection to `in-progress`; in a whole-PRD workstream, children move to `in-progress`
only as work on them actually begins. A new question after start moves the owning card
to `need-info`; an unmet adjacent prerequisite moves it to `blocked`. The tracker owns
reasons and return-state semantics; do not duplicate them here.

Before coding, state `Source: <user-explicit or canonical link>` and, for new or changed
user-facing behavior, briefly define:

- **Surface** — the existing interface;
- **Action** — the user's action;
- **Visible result** — what the user will see and be able to use;
- **Background work** — only the minimum technical work;
- **Unchanged** — the UX, workflow, ownership, and data boundaries being preserved.

A new or relocated Surface, actor, Action, Visible result, or workflow, or an intentional
change to `Unchanged`, requires explicit user confirmation. A bugfix/refactor that
preserves an unambiguous existing contract does not require renewed approval.

Within the confirmed scope, independently choose routine, reversible implementation
details and carry the requested result through to completion. Do not stop for a possible
improvement or a formal checkpoint. Do not implement additional useful scope; briefly
suggest it after completion if it is still relevant.

## 3. Existing model and complexity stops

By default, preserve the existing product model, UI surface, actor, workflow, ownership,
data boundaries, delivery target, and dependencies. The absence of an explicit
prohibition does not authorize creating a second UI, relocating an action, adding a new
product flow, or changing a contract for technical convenience.

The following changes are not routine details and require every agent to stop until the
accepted contract is confirmed:

- a new UI surface, actor, or user workflow;
- a new category of data/owner/permission/retention or a public/versioned contract;
- a new operational topology: a standalone process, queue, scheduler, or state machine
  not required by the accepted technical task;
- a second/parallel adapter or pipeline, a new ownership boundary, or duplicate
  storage/projection/implementation;
- a dependency/runtime default with a material maintenance/resource/compatibility
  trade-off;
- a field, abstraction, feature flag, or hook left in place after the current scope
  without an existing production writer/reader/consumer or one accepted in this task;
- a material expansion of the accepted scope.

The agent independently chooses a private adapter, schema detail, or local state within
an already accepted owner contract when the decision is reversible, follows an existing
pattern, does not change a data/ownership/public boundary, and does not create a second
path.

Keep an unused production element only for an already accepted named consumer. If the
project task/documentation policy defines a registration threshold and the related
deferred work crosses it, reference a canonical item or create one in accordance with
the policy.
If no such policy exists, briefly report the follow-up without inventing a tracker or
creating a document solely for a field or abstraction. Test-only use does not count as a
production consumer. Do not retain a duplicate projection "for the future."

When independently choosing the next work, prioritize a user-visible vertical slice.
Choose an infrastructure/evidence-only task first only when it directly blocks that
slice.

## 4. User-owned manual usability gate

A full manual usability gate is mandatory for a new capability, a changed primary
Action/Surface/Visible result, or a new waiting/result state. For a localized copy,
visual, or accessibility fix, focused UI inspection is sufficient. The user starts the
app and performs all manual UI verification. The agent runs appropriate automated
checks but does not open the app/browser for manual acceptance.

After implementation, prepare concise test cases on the existing interface to verify:

1. the user's Action is available on the accepted Surface;
2. if the operation genuinely takes time and progress is part of the accepted contract,
   progress neither obscures nor blocks the primary path; otherwise, do not add new
   progress UI;
3. the successful Visible result matches the accepted brief and is usable.

At the end of the work, put the test cases directly in the reply to the user: actions,
expected visible results, and material failure states based on actual risk. Keep the
manual gate pending until the user reports its result; do not present automated checks
as manual acceptance.

In the final response for a user-facing task, explain in plain language what is available,
where it is, what to click, what will be visible, and what material limitation remains.

## 5. Tests, E2E, and auxiliary complexity boundaries

### Regression protection

An automated regression test is mandatory for security, privacy, authorization,
ownership, data-loss, and recoverability risks. If such a test is technically impossible,
record an explicit blocker: do not call manual evidence automated, and allow ready only
under a user-owned exception that includes the reason and a follow-up task. In other
cases, add a test when it protects a stable contract and is proportionate to the risk.
For a typo/docs change, a one-off tooling/config error, external instability, or a
harness more expensive than the fix, a targeted/manual check is acceptable with a brief
reason for not adding a new test.

Give each risk one primary cheapest reliable test level. An additional unit, contract,
integration, E2E, or performance level is allowed only for a different boundary or
failure mode. Do not repeat the same corpus/invariant merely for evidence completeness.

### New E2E

1. First run: one happy path and the minimum accepted contract assertions; no fault
   injection, corpus, resource acceptance metrics, or performance claims.
2. After establishing a stable automated happy path, add one
   critical failure mode at a time.
3. Add corpus/performance characterization only for a separately accepted risk/claim
   after the minimum path is stable.
4. When a test fails, first classify production failure versus harness assumption; do
   not change the production contract merely to pass your own check.

A harness iteration is a change to its design/contract assumptions followed by a full
run of the path. A syntax typo does not count as a separate design iteration. After two
failed design iterations of one approach, name the disproven assumption and choose a
simpler existing path or ask the user. A third patch without a new hypothesis is
prohibited.

### Complexity boundaries

Do not compare production and auxiliary code by line count or create a LOC gate. Before
the first successful manual gate, limit work to the production path and proportionate
checks for current risks; do not add a new bespoke runner, fault framework, corpus,
benchmark, or evidence system.

After the gate, every new auxiliary entity must protect one named current risk/contract,
use the nearest existing test level, and not duplicate another check. A second new
runner/framework or an expanded corpus requires a separate accepted justification;
"evidence completeness" and hypothetical future utility are insufficient.

Production complexity is likewise not measured by LOC. A standalone production
abstraction, persistent state, process, service, or new execution path must have a
current accepted consumer and a direct role in the requested result. A routine private
function/type/adapter within one accepted path remains a routine detail when it is
reversible and creates no new boundary. Remove an unjustified standalone entity or
bring it forward for confirmation.

Performance measurement is needed only for an accepted SLO/capacity/cost/support claim,
a known hot path/constrained workload, a new resource-sensitive mechanism, or an
observed budget regression. Start with a simple baseline and focused measurement; do not
create benchmark infrastructure for a routine UI/correctness/refactor change.

## 6. Checks and CI

Use three levels:

1. **Agent checks** — diagnostics and minimum targeted tests/lint/typecheck for the
   changed behavior/owner; include dependent layers only for a contract change.
2. **Pre-commit** — fast deterministic checks selected by staged paths; no services,
   database/browser E2E, production builds, benchmarks, or full-verify fallback.
3. **PR CI** — draft runs inexpensive static/unit/docs checks; ready runs broad
   affected-layer gates. Do not call manual usability or explicit browser E2E "CI" if
   the workflow does not actually run them.

A full repository verify is needed only for a genuinely cross-layer/risky infrastructure
change, release, or explicit manual run. Do not run it after every commit. Do not claim a
check passed if it was not run.

Do not call a pre-commit check selected by staged paths but reading the entire working
tree/package "staged-content isolation": unrelated unstaged failures must not block the
commit. The hooks/CI composition may be changed only in a separate, explicitly assigned
governance task; routine work must not silently bypass it.

## 7. Subagents and orchestration

Subagents are disabled by default. Two independent justifications are allowed:

- actual parallel work with non-overlapping write scopes;
- independent expertise/review of a complex decision, even when the coordinator waits
  for the result.

Routine reading, a design checkpoint, or work the primary agent can quickly perform is
not sufficient justification. Before launching a subagent, state in one sentence why it
is needed, the specific result it will return, and—only for parallel work—what the
coordinator will do concurrently.

Editing workers use separate branches/worktrees or proven disjoint write sets. The
coordinator owns shared files, dependency order, integration, and readiness. Preserve
one session per task; send feedback back into that session. Place a review boundary at
product/architecture ambiguity, scope expansion, and before integration, not as a fixed
set of ceremonies. A worker does not self-approve readiness and does not merge/release/
deploy.

## 8. Git, commits, and PR

Explicit confirmation of the execution brief and transition of the selected PRD/task
to `in-progress` grant task-scoped authority to create/use a branch and, when needed,
an isolated worktree, make coherent commits, push, and create/update a PR without
separate questions for each action. Equivalent authority may come from a direct request
or narrower project policy; project policy may restrict this default. Loading the skill,
a `planned` status without start confirmation, or grooming-only work does not grant
this authority. Destructive reset/delete/force, merge, release, and deploy always
require separate authority.

- Commit a coherent, reviewable, revertible unit, not after every message or internal
  step. Do not mechanically split an atomic cross-layer vertical slice when intermediate
  commits would be inconsistent; follow the project's actual commitlint rules.
- By default, complete planned commits and closure locally; immediately before a ready
  PR, fetch and integrate the current base, resolve conflicts, run risk-based ready
  checks, and publish the completed branch. An early remote PR after `in-progress` is
  permitted but not required; if opened before scope is complete, it is always draft.
- Plan the first publication so one final PR CI run should be sufficient. Additional
  pushes and CI runs are allowed for a discovered defect, CI failure/flake, review
  change, conflict, or material base update; do not hide a necessary fix to preserve a
  formal run count.
- When task-scoped authority is used for early publication, collaborative review, or a
  remote-only check, create a draft. While the user is sending consecutive batches of
  the same work or known scope remains open, keep the PR draft. Do not switch between
  draft/ready after every batch. No separate confirmation is required to open this PR
  after `in-progress`.
- Before marking a draft ready and before merge, fetch and integrate the current base,
  resolve conflicts, and run risk-based ready checks.
- Update PR metadata only for a material change in scope, blocker, or readiness. A
  routine push does not require a separate body update.
- Incomplete published scope is draft; completed scope after the boundary is ready.
  Merge/release/deploy do not follow automatically from ready.

Routine tracked edits are recoverable from Git and do not require a global
`git stash -u`. Before destructively moving/deleting/overwriting substantial uncommitted
work, use a minimal scoped checkpoint: a commit, patch, or exact copy. Do not capture
someone else's untracked files or transfer a stash between worktrees.

Change the changelog/version only under the project release policy. Do not edit generated
sources manually.

## 9. Handoff and context

A handoff is needed only for an actual transfer/pause between sessions, agents, or
worktrees. Durable scope, task status, acceptance, decisions, and delivery state remain
in the canonical task/PR/Git; the handoff does not copy them or become a second source.

In a project that permits parallel work, a single tracked mutable pointer such as
`current.md` is prohibited: there is no global "current" workstream. The default is a
gitignored worktree-local file, for example `.agents/local/handoff.md`. It contains only
the worktree/branch identity and, when available, task/PR; the last confirmed commit, a
brief local dirty state, one next action, temporary blocker/tool state, and relevant
files. Do not commit it or merge it into `main`. Before the first write, verify that the
path is actually ignored; if it is not, configure a narrow ignore in an authorized
`init`/`migrate` action or use an already excluded local path. Do not create an empty
handoff during adoption merely to test the mechanism.

On resume, select a handoff only by the exact current worktree + branch and matching
task/PR, when specified; never select one by recency, the name `current`, or because it
is the only file found. A mismatch means ignoring the handoff entirely; read the
canonical task/PR separately. For transfer between machines or inaccessible worktrees,
use an explicit reference to the task/PR/branch and, when necessary, one brief PR/task
update rather than a shared repository handoff.

Do not update the handoff after every internal step. Delete the local file after a
successful resume or completion of the work. Editing agents on the same task use
separate branches/worktrees; the coordinator receives commits/PRs and a short result,
not a shared mutable handoff. During migration, first remove any unique durable state
from a legacy singleton handoff, then remove it from the active route within the agreed
scope.

## 10. Completion

A task is complete when the requested result exists, targeted checks have passed, the
user has confirmed the manual gate for user-facing behavior, scope has not been silently
expanded, and actual blockers have been named. Keep manual acceptance pending until the
user replies. If the work implements or changes a
documented contract, perform the applicable project closure reconciliation before
`done` and a ready PR; if no separate procedure is defined, compare the result directly
with the canonical PRD/task/TD/ADR. Any unresolved discrepancy is a blocker.
Do not copy that documentation governance here. Do not require the entire product phase
to close for a single request.

The final response briefly states the result, affected files/PR, checks performed,
material limitations, and concrete manual test cases for user-facing work. Call out the
grooming decisions that the user will see and should verify; this summary does not
replace their canonical record. Do not list process for process's sake. If an obvious next step
remains, offer it as a question; do not perform it without scope/authority.
