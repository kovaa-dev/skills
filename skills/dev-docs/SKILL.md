---
name: dev-docs
description: >-
  Maintain existing project documentation in place without requiring init or migration,
  and manage a file-based task tracker without duplicating requirements.
  Use for shaping a new product through grooming and decision agreement,
  supporting a minimum commercial launch, creating and updating PRDs, layer tasks, and
  TDs/ADRs, registering and prioritizing bugs by severity, technical findings, and product
  ideas, post-release maintenance and development, auditing documentation consistency,
  migrating and updating documentation rules while removing stale local duplicates,
  and preparing independent task tracks.
---

# dev-docs


## Establish context before making changes

1. Read the applicable project instructions. When available, locate the documentation index,
   canonical policy, layer registry, and affected cards/decisions. In an empty project,
   the absence of these files, established layers, and code does not block init or discover.
2. Determine the action and request boundaries. Installing or invoking the skill does not by
   itself authorize restructuring the project. If the goal is undefined, propose an option
   or perform a read-only audit; do not begin a broad migration.
3. For routine work, follow the existing project rules and the
   [maintenance without adoption contract](references/adoption.md#routine-maintenance-without-adoption).
   If the project has adopted the skill as its governance, load its complete project-local copy
   or pinned public source. Adoption and migration require a separate request; do not make them
   prerequisites for maintenance or create a mode/profile.
4. Do not invent requirements, owners, accepted decisions, deadlines, a stack, or constraints.
   Record unknowns as open questions. Do not create sample tasks from templates.

Justify every new product or technical choice and explicitly agree it with the user according
to the policy's "Decision approval" section. Applying already approved rules does not require
renewed agreement; do not treat your own proposal as an accepted decision. Determine the
permitted write mode first.

## Selective loading

Read only the references you need; the paths below are relative to the skill directory:

- Granularity for every document you create and the minimum-context route: the "Granularity
  of any document" section in [documentation](references/documentation.md). Apply it when
  creating, splitting, and reading cards, decisions, research, reports, indexes, and the
  references themselves; one layer does not mean one enormous file.
- General rules, canonical ownership, and change maintenance: the same policy.
- PRDs, layers, IDs, statuses, dependencies, and acceptance: the
  [task tracker](references/task-tracker.md).
- Bugs, findings, ideas, and post-release work: [maintenance](references/maintenance.md);
  for short cards, see [intake forms](references/forms-intake.md). First determine whether
  the issue requires separate registration; do not create a card for every locally resolved
  defect or irrelevant idea.
- New or existing products, backlog grooming, start briefs, and incremental delivery:
  [product formation](references/product-discovery.md).
- A factual question requiring multi-source/version/conflict research, or consuming its result:
  [bounded research handoff](references/research-handoff.md).
- Adoption or migration: [bootstrap](references/documentation-system-template.md), then the
  required normative sections linked from it.
- Creating a card/index: select one file from the
  [forms index](references/documentation-registers-template.md).
- Integrating an existing limited parser: [optional compatibility](references/validator-compatibility.md).
  Do not load this reference during ordinary work that does not use such a tool.

For maintenance without adoption, use relevant guidance within the existing project conventions;
the skill's tracker schema and forms do not require converting existing documents. After adoption,
read either the project-local copy or the pinned public canonical source, not stale policy
duplicates. Do not load the entire backlog for one card.

Routine documentation maintenance is the default when helping with existing project work,
including keeping affected docs consistent with implementation and accepted decisions. It needs
neither a separate action nor prior init: follow the
[maintenance contract](references/adoption.md#routine-maintenance-without-adoption), within the
current task's write authority. Use the actions below only when their outcomes are requested.

## Actions

- **discover** — move from an idea or the current state through grooming to incremental
  feature delivery. It works without init: discussion results remain in responses, while write
  permission allows the minimum agreed documents. For a new product, propose
  `Alpha/Beta/RC/Release/Next`, but agree or adapt the stages; do not impose retrospective
  labeling on an existing product. Overall grooming sets direction and unblocks the nearest minimally usable result.
  Perform focused grooming for a selected `backlog` PRD/task and move it to `planned`
  only after the result is accepted; the tracker defines the required acceptance source, `need-info`,
  and dependency `blocked`. When starting `planned` work, do not repeat grooming:
  restore context, present a short execution brief, and after confirmation move the
  selected PRD/task to `in-progress`. Make local and distant decisions closer to
  implementation. A minimal backlog PRD may be registered earlier without presenting
  it as a ready contract.
- **init** — identify the minimum settings and propose a structure. When adoption is requested,
  create the minimum docs/task settings, ask the user to choose "copy in the repository" or
  "link to the published skill," and agree and apply the automatic project entrypoint under the
  active project-work policy. If that policy does not grant authority, request permission. Once
  verified, the skill loads during ordinary docs/task/decision work; the user does not invoke it
  manually. Do not create a separate mode/profile or a third paraphrased copy. Without product
  grooming and migration, layers may still be undefined; cards and decision indexes appear only
  as they become necessary.

- **audit** — a useful standalone read-only documentation-consistency action before deciding
  whether to migrate. Without making changes, inspect the selected scope and report issues with
  paths, conflicting formulations, consequences, and a proposed fix. Within the scope, classify
  and inspect every document type
  regardless of directory: product/marketing/backend/frontend,
  README/runbook/spec/research/verification records, PRD/tasks/TD/ADR, indexes, and templates. A full audit
  covers every document in the repository; an affected-scope audit covers every related document
  type, not only technical sources. First check project documentation for internal contradictions
  according to the "Project documentation consistency check" section, then compare the
  applicable rules. For every contradiction, show both formulations, scope, practical effect,
  recommendation, and alternative; discuss the choice with the user rather than resolving the
  conflict yourself. Refine existing TODO/backlog findings into a proposed dependency-ready task
  map: show non-blocking tracks, prerequisites, and the required integration boundary separately.
  Audit canonical ownership, document status, links, duplication, contradictions, and task/decision
  consistency; do not use this action to establish the truth or completeness of underlying factual
  claims, perform corpus-wide research, or certify product/code/security behavior. When such a
  conclusion is required, use the [bounded research handoff](references/research-handoff.md)
  and keep the documentation conclusion open until a source-grounded result is available.
  An audit does not create cards or launch agents without write permission/project-work authority.
  For adoption, verify the normal affected-scope criteria or, when explicitly required, the full
  depth described in the adoption reference. An ordinary audit of one area does not certify the
  entire project.
- **migrate** — agree the boundaries and duplicate cleanup. It includes an affected-scope audit;
  no separate preliminary audit run is required. Perform
  [rule consolidation](references/governance-migration.md): first check the internal consistency
  of related project docs, then find rules in instructions, documents, and templates; present
  conflicts to the user and preserve unique rules in canonical sources. After the user's decision,
  delete/replace conflicting active rules and semantic duplicates in the agreed scope; do not
  leave them beside the new source as supposedly safe history.
  Preserve a recoverable checkpoint and move content in small batches using copy/move operations
  and targeted edits. Before execution, classify every document in the agreed scope and break
  TODO/backlog/remediation work into independently executable tasks with explicit prerequisites,
  owner scope, and acceptance. Non-blocking tracks may be identified for parallel implementation;
  when they have a shared boundary with its own result, create a dependent integration task. Do
  not create integration ceremony for trivial assembly, and do not treat the task map as authority
  to launch agents automatically—orchestration belongs to the active project-work policy. By
  default, reconcile only active changed rules/cards and keep a compact mapping in the
  PR/task/settings; a separate complete migration-coverage mapping is required only for a full/large
  migration or explicitly required policy traceability. Do not claim a partial migration is
  complete. When explicitly requested, **migrate hard** may rename the ID/path/title of already
  closed tasks and product phases according to
  [hard migration](references/governance-migration.md#hard-migration-names-and-ids-of-historical-documents),
  preserving their status/checklist/verification records; commit hashes/messages and PR numbers/URLs do not
  change.
- **update** — when the verified skill revision changes, perform an affected-scope audit + migrate
  according to the [update rules](references/adoption.md#update): classify added/strengthened/
  weakened/removed/moved rules, discuss conflicts, and remove stale docs/task copies, templates,
  and parser rules. Perform hooks, CI, handoff, Git, and other agent automation only under the
  active project-work policy. A weakened or removed rule must not remain locally in effect without
  an explicitly accepted scoped exception. Update the revision only after verifying the result.

An available skill can be selected during ordinary work without adopting it as project governance
or requiring a manual invocation for each edit. Verified adoption additionally provides a
reproducible project entrypoint and makes the selected source canonical. Changing the source skill
requires a separate request; project exceptions do not silently override it.

## Execution checks

Run only the affected checks from the selected references and the local project, under the
applicable project conventions. Do not create a tracker or index just to run these checks.
For an adopted tracker, verify links, IDs, and dependencies for affected cards; ensure the task
index matches the agreed roadmap, each registered task is visible exactly once, status projections
match canonical cards, and indexes do not contain a second plan or contract. A full graph scan is required only for an explicitly full
migration/audit scope. Check semantic completeness of the documentation against its declared
sources separately: successful lint does not prove it. Do not call proposed work accepted or a
task done without completed acceptance, a verification record, and the applicable implementation
reconciliation with canonical decisions under the
policy's "Implementation closure reconciliation" section.

When work spans multiple batches, check direction against the request after each batch. For an
ordinary migration, progress and compact mapping in the existing PR/task are sufficient; a
separate card is optional. A separate temporary migration-coverage file is required only for a
full/large migration or required traceability, and at completion it is either condensed or retained
as a historical migration record according to policy. Do not create a duplicate log or log tree.

Orchestration, worktrees, checks, commits, and the PR lifecycle belong to the active project-work
policy. `dev-docs` develops dependency-ready task tracks, non-blocking parallel work, and any
necessary integration task, but it does not launch subagents or alter the delivery process by
itself. When delegating, it supplies the canonical task, sources, dependencies, acceptance, and
docs scope; the project or an available execution workflow determines actual write scopes, agents,
and integration review.

Do not delete sources without permission and verified recovery. Commits, pushes, and publication
follow the active project-work policy, an explicit request, or stored project authority:
`dev-docs` neither grants nor revokes these permissions. Do not modify the skill itself during
ordinary project documentation work.

## Optional request parameters

These are natural language, not CLI or typed arguments:
`action`, `scope`, `mode: proposal/read-only/apply`, `language`,
`batch size`, `constraints` (for example, no deletion or commits).
When parameters are absent, follow the explicit request and project settings; do not ask for all
of them again. Store persistent settings in the project's existing settings source, or the
documentation index when adopting the skill; maintenance does not require a new settings file.

## Package boundaries

The skill contains only Markdown, with no validators or runtime. Use available project checks or
explicitly describe manual verification. Automation helps catch mechanical errors, but it does not
replace semantic review and must not be installed implicitly. Adapt example paths and metadata to
the project; do not let a nonexistent tool dictate them.

When adopting the skill as project governance, use either a complete project-local copy or an
explicitly selected pinned link to a public source. The method is evident from the project
structure and is not duplicated in a state field. Do not assume that a personal absolute path is
available to the team/CI; the adoption requirements define reproducible access and behavior when
the source is unavailable. Routine maintenance does not require adopting either method.
