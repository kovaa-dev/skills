# Bootstrap for documentation, requirements, and queues

Use [governance](documentation.md), [requirements](requirements.md), and
[work queues](work-queue.md). Reuse compatible sources and reconcile selected material
through [source assessment](source-transition.md); an explicit full transition uses
[migration](governance-migration.md).

## Minimum setup

Determine the agreed result and discussion/write authority. Init is not a prerequisite
for grooming or ordinary maintenance. Reuse existing project paths and documents.
Select material under [documentation purpose and ownership](documentation.md#documentation-purpose-and-ownership).
Create/update only documents needed for the actual question, obligations, and registered
work. Navigation, decision/artifact directories, and history files appear with real content;
a documentation-only correction does not require a new specification or queue.

Illustrative placement, not a mandatory tree:

- docs/wiki/personal-settings.md: related requirements and shared rationale.
- docs/reference/settings-api.md: sourced API behavior, when readers need that reference.
- docs/operations/settings-sync.md: operation/diagnosis/recovery procedure, when useful.
- Existing queue/task index, or docs/queue.md when none exists: lean work and result links.
- docs/architecture/decisions/: independently useful decisions, if needed.
- docs/development/documentation-index.md: navigation/settings, if the project needs it.

Use [ID namespace rules](documentation.md#layers-and-id-namespaces): new layer-based
requirements use `R-<LAYER>-NNN`; existing work/source IDs keep their conventions.
Without established layers, use the documented fallback rather than inventing a registry;
task IDs identify execution rows and link requirement revisions under
[queue rules](work-queue.md#one-work-item-one-result-boundary).
Reuse existing layer definitions; no empty registry, root redirect, or file per work item
is required. Multiple queues are allowed with one canonical
entry per item and cross-queue waits.

## Agent entrypoint when authorized

Use the project's existing automatically read entrypoint. State the selected skill
source and the new normal route in one concise pointer. For example:

> For product/technical documentation, requirements, work queues, and decisions, read
> the selected dev-docs source and its material/owner route. Assess selected sources,
> reuse compatible owners, and reconcile missing contract/work ownership before continuing.
> Preserve source meaning and history. Do not migrate unrelated
> backlog implicitly. Keep old and new work in the existing queue, updating selected
> entries in place; use an explicit migrate request for a one-shot transition.

Adoption uses a complete project-local copy or a pinned public source under
[adoption](adoption.md). Do not copy the whole policy into AGENTS/RULES. Make entrypoint,
hooks, CI, or Git changes only with the active project-work authority. Existing copy/pin
selection does not need to be requested again for ordinary maintenance.

## Existing projects

Keep [the existing queue/index](work-queue.md#existing-queues-during-transition) as the
shared selection route. Adding new work does not require converting unrelated entries.

Classify existing obligations, plans, technical decisions, source facts, verification,
and navigation by meaning. Any document may contain a valuable contract, historical
work, or both. Capture only the selected scope into appropriate owners; preserve
acceptance, exceptions, questions, historical results, and useful descriptions/procedures.
Use [range-specific conversion notices](source-transition.md#convert-before-continuing)
so unconverted parts remain discoverable and active.

A local conversion does not require reorganizing every directory or claiming that the
whole project adopted the new source. State any binding old-format conflict. Read-only
discovery produces a proposed transformation, not converted files.

## Checks

Check real links/anchors, stable IDs, definition versus execution state, requirement
applicability, concrete prerequisite suppliers, result/verification links, and the
source-to-current route. New specifications and work must be usable without superseded source text
as required context. Existing parsers must be adapted rather than allowed to regenerate
incompatible source formats. Use only tools actually available in the target project.
