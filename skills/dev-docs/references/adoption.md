# Adoption, updates, and ordinary maintenance

Requirements/specifications and lean queues are the current model. Old PRD/task tracking
is officially legacy; selected legacy work follows [on-touch conversion](legacy-transition.md).
A full backlog transition uses the separately requested [one-shot migration](governance-migration.md).

## Routine maintenance without adoption

Selecting dev-docs for authorized work does not require init, a global policy migration,
or an adoption-mode field. Maintain the affected scope using
[documentation purpose and ownership](documentation.md#documentation-purpose-and-ownership):

- Preserve compatible project paths, language, stable IDs, accepted meaning, history, and
  explicit constraints. Reuse existing specifications/wiki and queue locations.
- Before continuing selected legacy work or an uncaptured requirement, perform the bounded
  conversion. Keep unrelated legacy records available with an explicit route to the new model.
- Faithful capture of an existing accepted contract is continuity, not a new product
  decision. Do not ask again merely to convert the selected item or start already
  authorized work. Do not infer write permission from a read-only request.
- Create only material needed for the actual question/contract/result; no empty indexes, layers,
  PRDs, or ADRs to satisfy a template.
- Do not change binding agent instructions/hooks/CI or bulk-delete/restructure sources
  without the corresponding scope. If explicit project constraints prohibit conversion,
  show the exact conflict and proposed minimum change; do not claim conversion or silently
  continue the affected implementation under a duplicate hidden tracker.

A source pinned to an older skill revision remains that project's selected source until
an authorized update. Installing this revision does not silently rewrite consuming projects.
These limits do not make routine authorized documentation maintenance depend on init.

## How a project adopts governance

Explicit init/adoption selects one reproducible method:

- **Copy in the repository:** the complete skill directory at a project-local path,
  committed and linked by the entrypoint; propose this default when no method was chosen.
- **Pinned public source:** a public source at an immutable Git SHA/content digest,
  chosen explicitly or required by organization policy. Mutable branches/latest/tags
  without immutable targets and personal machine paths are not reproducible governance.

Do not store a separate mode/profile/rule-source registry. The copy or pinned pointer
makes the method evident. Ask only when adoption or a change of source is actually
requested and the choice is not already authorized.

Requirements, queues, decisions, artifacts, history, and local settings remain project
content. General governance has one canonical source; do not keep a paraphrased third
policy. Old task cards may remain unconverted after governance adoption, with explicit
on-touch routing; adopting a source is not proof of a fully migrated backlog.

## Safe adoption and verification

1. Identify the affected rules, contracts, entrypoints, templates, and actual parser checks.
2. Compare related accepted project sources, preserve unique settings/exceptions, and
   resolve conflicts with their authorized owner. A format difference is not automatically
   a product conflict.
3. Apply the authorized copy/pointer and entrypoint/settings changes. Clearly state the
   new default and the legacy conversion route. Execution policy owns agent/CI/Git changes.
4. Verify affected links, source availability, requirement/work identity, canonical state,
   applicability, and one ordinary request route.
5. Claim only the achieved scope. If governance update or content conversion is partial,
   list the remaining boundary; keep unresolved sources accessible without presenting
   duplicate active contracts.

Full verification is required for an explicitly full migration/audit or an actual project
policy requirement. It covers all source types/ranges in scope, preserved questions,
acceptance/verification, cross-links/dependencies, real enforcement, and residual legacy
routing. It checks the documentation system, not product/security correctness.

Detailed working coverage is used when migration scope or required traceability warrants
it. Condense transient detail under the [coverage protocol](legacy-transition.md#coverage-and-reconciliation),
keeping checked provenance accessible. It is not a permanent migration mode or live tracker.

## Update

For an authorized source revision update:

1. Locate the installed copy/pinned source and compare actual revisions. If the previous
   source is unavailable, state that limitation and audit the current affected rules.
2. Classify added, strengthened, weakened, removed, and moved rules. Find consumers,
   templates, old instruction copies, parser assumptions, and source availability.
3. Resolve material conflicts, update the canonical owner, then consumer references and
   applicable settings in one coherent change. Preserve accepted scoped exceptions;
   do not keep obsolete stricter requirements silently active.
4. Update skill copy/pointer and affected routing to requirements/queues. Remaining legacy
   work follows on-touch conversion; run the separate migrate action only when full
   content conversion was requested.
5. Verify the affected routes/checks and then finalize the pinned revision or committed
   copy. Do not claim completion if the selected source is inaccessible or links still
   direct new work into old task authoring.

Coordinated changes with project-work governance update the owning rule once and link
consumers to it. This skill does not require a particular execution skill or gain
permission to merge, release, or deploy from adoption.
