---
name: dev-docs
description: >-
  Maintain requirements, specifications, lean work queues, decisions, and verification
  without duplicating contracts. Use for product grooming, documentation maintenance,
  bugs, research and other deliverables, change-impact and consistency checks.
  Before continuing selected legacy task/PRD or undocumented-requirement work,
  convert its affected scope to requirements and queue entries. Use migrate for an
  explicitly requested one-shot transition; legacy task tracking is deprecated.
---

# dev-docs

## Default model and first action

The current model is requirements-driven: specifications describe the agreed result,
queue entries request work, and artifacts/verification record what was delivered.
PRD/product-task and layer-task tracking is officially **legacy**. It remains readable
only while unconverted records remain; do not create new legacy cards or extend that
workflow as the default.

1. Read applicable project instructions and the selected canonical skill source. Respect
   explicit project/user constraints, existing paths, language, and accepted contracts.
2. Identify the selected work and affected contracts. Before changing or executing a
   legacy task/PRD, or continuing work on a requirement not yet captured in this model,
   follow [on-touch conversion](references/legacy-transition.md). Do this within the
   authorized work; no init, full-backlog migration, or new permission ceremony is needed.
   Read-only requests produce a proposal only. An explicit prohibition on migration or
   a conflicting binding project instruction must be surfaced, not silently bypassed.
3. Continue from the resulting specification/requirement and queue entry, not the old
   card. Reuse an existing canonical record and conversion mapping before creating one.
   Do not migrate unrelated linked history merely because it was encountered.
4. Do not invent accepted requirements, owners, constraints, implementation evidence,
   approval, or missing historical facts. Preserve unknowns as questions.

This entrypoint, forms, bootstrap, and migration references all use the new model.
[Legacy recognition](references/task-tracker.md) is a compatibility route into conversion,
not a second supported authoring workflow. Source-skill changes do not automatically
rewrite an installed pinned copy or every consuming project.

## Read only what the work needs

- Canonical ownership, decision approval, history, proportionality, and document
  granularity: [documentation governance](references/documentation.md).
- Requirements, specification files, stable IDs, revisions, rationale, applicability,
  implementation prerequisites, conflicts, and impact analysis:
  [requirements](references/requirements.md).
- Work selection, readiness, cross-queue waits, research and non-code results,
  completion/history, and delivery targets: [work queues](references/work-queue.md).
- Selected legacy work or an uncaptured requirement:
  [on-touch conversion](references/legacy-transition.md). Read old-format details in
  [legacy recognition](references/task-tracker.md) only as needed.
- Grooming and incremental product development:
  [product discovery](references/product-discovery.md).
- Bugs, findings, ideas, severity, and releases:
  [maintenance](references/maintenance.md).
- Source-heavy factual questions:
  [bounded research handoff](references/research-handoff.md).
- Explicit one-shot migration:
  [migration](references/governance-migration.md).
- Adopting/updating the skill as project governance:
  [adoption](references/adoption.md) and [bootstrap](references/documentation-system-template.md).
- Optional examples: [forms](references/documentation-registers-template.md).
- An existing parser that actually constrains the work:
  [validator compatibility](references/validator-compatibility.md).

Do not load the entire backlog, all references, or every linked document for one change.
Use the affected area and its applicable constraints; follow dependencies/consumers only
where they affect the result. Compact reading must still preserve cross-cutting contracts.

## Ordinary work and actions

Ordinary maintenance is the default: capture/convert the affected scope, maintain its
requirements and queue entry, then reconcile documentation with the delivered result.
Preserve compatible project conventions without requiring adoption. A file rewrite or
whole-repository reorganization is not implied by this routine path.

- **discover** — refine an idea/current product into draft or accepted requirements,
  open questions, and the nearest useful deliverable. Groom specifications and prepare
  work separately; unknown implementation can become research without changing an
  accepted product requirement to draft. Respect discussion/read-only mode.
- **init** — when explicitly requested, adopt the minimum requirements/wiki and queue
  entrypoints through a complete project-local skill copy or a pinned public source.
  Create only needed documents; no layer registry, empty template tree, or legacy tracker.
- **audit** — read-only consistency and impact review of the selected scope. Classify
  specifications, requirements, decisions, queues, artifacts, and legacy sources by
  meaning, regardless of directory. Show conflicting formulations, applicability,
  consequences, and proposed resolutions. Do not certify factual claims or product
  behavior without the necessary source-grounded research/verification.
- **migrate** — explicitly convert the entire agreed scope in one controlled operation
  using [the migration workflow](references/governance-migration.md). Preserve semantics,
  acceptance sources, history, and recoverability; reconcile all in-scope links and work.
  This replaces the former task-schema/rename migration. A request named "migrate hard"
  routes to this same workflow, with destructive cleanup only when explicitly authorized.
- **update** — compare the selected skill revision, update affected governance consumers
  and forms, and retire conflicting old routing under [adoption](references/adoption.md).
  Installing/updating rules does not imply a full backlog conversion: remaining legacy
  records follow the on-touch path unless a one-shot migration was requested.

For already accepted, authorized work, a short execution brief restores scope, expected
result, affected contracts, and checks. The user's request may already authorize that
same work; do not ask again merely to change a status. New product/public/ownership
choices require their normal acceptance. Routine reversible details remain independent
engineering choices.

## Completion and boundaries

Before closing work, reconcile the delivered result against the applicable requirement
revisions and preserved contracts. Keep verification next to its owning specification
or artifact; the queue holds a concise result link. Historical completion is not proof
of the current revision. Research completion is not implementation completion.

Check affected links/anchors, ID uniqueness, requirement/work dependencies, canonical
queue ownership, conversion redirects, and current versus historical applicability.
Successful lint does not prove semantic compatibility. State unconverted scope, unresolved
conflicts, missing sources, and verification limits honestly.

Git, worktrees, agents, CI, PRs, release, and production delivery follow the active
project-work policy. This skill defines what must be captured and verified; it does not
mandate PR-based delivery, install a runner, or grant merge/deploy authority. Code,
documents, datasets, research, configurations, and external actions can all be outputs;
publication and completion depend on the agreed target and actual confirmation.

The package provides Markdown guidance and examples. It does not claim that indexes,
backlinks, conflict discovery, or synchronization are automated unless a project actually
implements them. Do not create a new tracker/runtime solely to satisfy this skill.
