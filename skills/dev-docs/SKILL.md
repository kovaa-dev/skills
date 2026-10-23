---
name: dev-docs
description: >-
  Maintain product and technical documentation, requirements, lean work queues,
  decisions, and verification without duplicating contracts. Use for product grooming,
  references and guides, recovering requirements from code, bugs, research, change-impact
  and consistency checks.
  Before continuing selected legacy task/PRD work or carrying forward obligations from
  older noncanonical documents, convert the affected scope to requirements and queue entries.
  Capture new input directly in its owning documents. Use migrate for an explicitly
  requested one-shot transition; legacy task tracking is deprecated.
---

# dev-docs

## Default model and first action

The current work model is requirements-driven: specifications own obligations, queues
request work, and results record delivery/verification. Descriptions, API references,
guides, and runbooks maintain product/system knowledge through their own useful reading
routes. PRD/product-task and layer-task tracking is officially **legacy**: it remains
operational for unconverted scope, with historical sources still accessible afterward.
Do not create new legacy cards or extend that workflow as the default.

1. Read applicable project instructions and the selected canonical skill source. Respect
   explicit project/user constraints, existing paths, language, and accepted contracts.
2. Identify the reader's question and material type using
   [documentation purpose and ownership](references/documentation.md#documentation-purpose-and-ownership).
   Reuse its owning document; requirements and queue entries are created only when their
   meanings and registration rules apply.
3. Identify the selected work and affected contracts. Before changing or executing selected
   legacy work or carrying forward obligations from older noncanonical documents,
   follow [on-touch conversion](references/legacy-transition.md). Do this within the
   authorized work; no init, full-backlog migration, or new permission ceremony is needed.
   Read-only requests produce a proposal only. An explicit prohibition on migration or
   a conflicting binding project instruction must be surfaced, not silently bypassed.
4. Continue from the owning records for the selected scope. Reuse canonical documents
   and conversion mappings before creating anything.
   Do not migrate unrelated linked history merely because it was encountered.
   Resolve [current contracts, proposals, and history](references/requirements.md#current-contract-and-nonbinding-material)
   before treating found text as binding; follow retirement/replacement notices.
5. Do not invent accepted requirements, owners, constraints, implementation evidence,
   approval, or missing historical facts. Preserve unknowns as questions. Capture material
   new requirements/changes under [ongoing capture](references/requirements.md#questions-during-work).
   Recover undocumented behavior/constraints through
   [code recovery](references/requirements.md#recovering-requirements-from-code), with explicit provenance.
   Verify [coverage](references/legacy-transition.md#coverage-and-reconciliation) before
   claiming any selected legacy range transferred without loss.

This entrypoint, forms, bootstrap, and migration references all use the new model.
[Legacy recognition](references/task-tracker.md) is a compatibility route into conversion,
not a second supported authoring workflow. Source-skill changes do not automatically
rewrite an installed pinned copy or every consuming project.

## Read only what the work needs

- Documentation types, canonical ownership, decision approval, work-context placement,
  proportionality, and granularity: [documentation governance](references/documentation.md).
- Requirements, specification files, stable IDs, revisions, rationale, applicability,
  implementation prerequisites, proposal/retirement lifecycle, conflicts, and impact analysis:
  [requirements](references/requirements.md).
- Work selection, readiness, cross-queue waits, research and non-code results,
  completion/history, and delivery targets: [work queues](references/work-queue.md).
- Selected legacy work or obligations held only in older noncanonical documents:
  [on-touch conversion](references/legacy-transition.md). Read old-format details in
  [legacy recognition](references/task-tracker.md) only as needed.
- New requirements, clarifications, and material questions:
  [ongoing capture](references/requirements.md#questions-during-work).
- Finding and recording undocumented requirements from implementation:
  [code recovery and provenance](references/requirements.md#recovering-requirements-from-code).
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

Ordinary maintenance updates the material that answers the selected question. Capture
applicable obligations or convert selected legacy scope when needed; use the queue's
registration threshold for independently tracked work. A local documentation edit within
existing work does not need another R/Q record. Preserve compatible conventions without
requiring adoption or a whole-repository reorganization.

- **discover** — refine an idea/current product into draft, proposed, or accepted requirements,
  open questions, and the nearest useful deliverable. Groom specifications and prepare
  work separately; unknown implementation can become research without changing an
  accepted product requirement to draft. Respect discussion/read-only mode.
- **init** — when explicitly requested, adopt the needed documentation entrypoints through
  a complete project-local skill copy or a pinned public source.
  Create only needed documents; no layer registry, empty template tree, or legacy tracker.
- **audit** — read-only consistency and impact review of the selected scope. Classify
  descriptions, guides/procedures, specifications, decisions, queues, results, and legacy sources by
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

## Completion and boundaries

Use [closure reconciliation](references/documentation.md#implementation-closure-reconciliation)
for the selected result and material type. Work readiness, execution briefs, completion,
and history follow [work queues](references/work-queue.md); requirement revisions and
applicability follow [requirements](references/requirements.md).

Check affected links/anchors and, where those records exist, ID uniqueness, dependencies,
canonical queue ownership, conversion/retirement redirects, proposal separation, and
current versus historical applicability.
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
