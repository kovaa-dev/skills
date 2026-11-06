---
name: dev-docs
description: >-
  Maintain product and technical documentation, requirements, lean work queues,
  decisions, and verification without duplicating contracts. Use for product grooming,
  references and guides, recovering requirements from code, bugs, research, change-impact
  and consistency checks.
  Reconcile selected existing sources into owning requirements and work records when
  their semantics do not yet fit this model. Preserve compatible documents and capture
  new input directly in its owners. Use migrate for an explicitly requested one-shot transition.
---

# dev-docs

## Default model and first action

The current work model is requirements-driven: specifications own obligations, queues
request work, and results record delivery/verification. Descriptions, API references,
guides, and runbooks maintain product/system knowledge through their own useful reading
routes. Determine each project's source formats and authoritative owners from actual
material; no particular task or document scheme is assumed to be obsolete.
Keep the existing queue/index as the shared selection route for old and new work;
use [existing queues during transition](references/work-queue.md#existing-queues-during-transition).
Queues are linked ID/name/status rows; context and results stay at their linked owners.
The requirement owns its delivery status and the queue explicitly repeats it. For
independent work, its linked context owns the status. Before work, read the owner;
reconcile queue copies in its favor and update affected rows when the source changes.
[Work-bearing revisions](references/requirements.md#revision-delivery-and-history) use
`<requirement-id>@<n>` with their own status and mandatory queue row captured together.
They do not reopen prior deliveries; completed details remain linked outside the normal
current-contract reading route.
Register useful outcomes under the [queue rules](references/work-queue.md), not the
supporting record maintenance performed during the current work.
Use [requirement IDs and existing layer definitions](references/documentation.md#layers-and-id-namespaces):
new layer-based requirements use `R-<LAYER>-NNN`, numbered separately from existing work.
Preserve existing stable IDs unless normalization is requested; explicit project overrides apply.

1. Read applicable project instructions and the selected canonical skill source. Respect
   explicit project/user constraints, existing paths, language, and accepted contracts.
2. Identify the reader's question and material type using
   [documentation purpose and ownership](references/documentation.md#documentation-purpose-and-ownership).
   Reuse its owning document; requirements and queue entries are created only when their
   meanings and registration rules apply.
3. Identify the selected work and affected contracts. Before changing or executing selected
   existing material whose contract/work ownership does not fit this model,
   follow [on-touch conversion](references/source-transition.md). Do this within the
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
   new input under [ongoing capture](references/requirements.md#questions-during-work);
   agreed changes revise the [current requirement](references/requirements.md#updating-the-current-revision).
   Recover undocumented behavior/constraints through
   [code recovery](references/requirements.md#recovering-requirements-from-code), with explicit provenance.
   Verify [coverage](references/source-transition.md#coverage-and-reconciliation) before
   claiming any selected existing range transferred without loss.

This entrypoint, forms, bootstrap, and migration references all use the new model.
Source-skill changes do not automatically
rewrite an installed pinned copy or every consuming project.

## Read only what the work needs

- Documentation types, canonical ownership, decision approval, work-context placement,
  proportionality, and granularity: [documentation governance](references/documentation.md).
- Requirements, specification files, stable IDs, revisions, rationale, applicability,
  implementation prerequisites, proposal/retirement lifecycle, conflicts, and impact analysis:
  [requirements](references/requirements.md).
- Work selection, readiness, cross-queue waits, research and non-code results,
  completion/history, and delivery targets: [work queues](references/work-queue.md).
- Existing material that needs semantic reconciliation:
  [source assessment and on-touch conversion](references/source-transition.md).
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
applicable obligations or convert selected existing scope when needed; use the queue's
registration threshold for independently tracked work. A local documentation edit within
existing work does not need another R/Q record. Preserve compatible conventions without
requiring adoption or a whole-repository reorganization.

- **discover** — refine an idea/current product into draft, proposed, or accepted requirements,
  open questions, and the nearest useful deliverable. Groom specifications and prepare
  work separately; unknown implementation can become research without changing an
  accepted product requirement to draft. Respect discussion/read-only mode.
- **init** — when explicitly requested, adopt the needed documentation entrypoints through
  a complete project-local skill copy or a pinned public source.
  Create only needed documents; reuse existing layer definitions instead of creating an
  empty registry/template tree or parallel tracker.
- **audit** — read-only consistency and impact review of the selected scope. Classify
  descriptions, guides/procedures, specifications, decisions, queues, results, and source records by
  meaning, regardless of directory. Show conflicting formulations, applicability,
  consequences, and proposed resolutions. Do not certify factual claims or product
  behavior without the necessary source-grounded research/verification.
- **migrate** — explicitly convert the entire agreed scope in one controlled operation
  using [the migration workflow](references/governance-migration.md). Preserve semantics,
  acceptance sources, history, and recoverability; reconcile all in-scope links and work.
  Destructive cleanup requires explicit authorization.
- **update** — compare the selected skill revision, update affected governance consumers
  and forms, and retire conflicting old routing under [adoption](references/adoption.md).
  Installing/updating rules does not imply a full backlog conversion: remaining source
  records follow source assessment and the on-touch path when needed.

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
