# Bootstrap for documentation, requirements, and queues

Use [governance](documentation.md), [requirements](requirements.md), and
[work queues](work-queue.md). This guide creates the new scheme, not a legacy PRD/layer
tracker. Routine selected work uses [on-touch conversion](legacy-transition.md);
an explicit full transition uses [migration](governance-migration.md).

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
- docs/queue.md: canonical lean work entries and completed-result links.
- docs/architecture/decisions/: independently useful decisions, if needed.
- docs/development/documentation-index.md: navigation/settings, if the project needs it.

Requirements use stable R IDs and queue entries stable Q IDs across files. Existing
meaningful requirement IDs may be retained. No layer prefix registry, root redirect,
or file per work item is required. Multiple queues are allowed with one canonical
entry per item and cross-queue waits.

## Agent entrypoint when authorized

Use the project's existing automatically read entrypoint. State the selected skill
source and the new normal route in one concise pointer. For example:

> For product/technical documentation, requirements, work queues, and decisions, read
> the selected dev-docs source and its material/owner route. PRD/layer-task
> tracking is legacy: before continuing selected old work, convert its affected
> requirements/results and resume at the new canonical records. Do not migrate unrelated
> backlog implicitly; use an explicit migrate request for a one-shot transition.

Adoption uses a complete project-local copy or a pinned public source under
[adoption](adoption.md). Do not copy the whole policy into AGENTS/RULES. Make entrypoint,
hooks, CI, or Git changes only with the active project-work authority. Existing copy/pin
selection does not need to be requested again for ordinary maintenance.

## Existing projects

Classify existing obligations, plans, technical decisions, source facts, verification,
and navigation by meaning. A file named PRD may contain a valuable contract, historical
work, or both. Capture only the selected scope into appropriate owners; preserve
acceptance, exceptions, questions, historical results, and useful descriptions/procedures.
Use [range-specific conversion notices](legacy-transition.md#convert-before-continuing)
so unconverted parts remain discoverable and active.

A local conversion does not require reorganizing every directory or claiming that the
whole project adopted the new source. State any binding old-format conflict. Read-only
discovery produces a proposed transformation, not converted files.

## Checks

Check real links/anchors, stable IDs, definition versus execution state, requirement
applicability, concrete prerequisite suppliers, result/verification links, and the
legacy-to-current route. New specifications and work must be usable without old tasks
as required context. Existing parsers must be adapted rather than allowed to regenerate
the old schema. Use only tools actually available in the target project.
