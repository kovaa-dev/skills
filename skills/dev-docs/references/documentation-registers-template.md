# Specification, queue, and artifact forms

The current model is [requirements](requirements.md) and [work queues](work-queue.md)
under [documentation governance](documentation.md). Use only the example needed now.
Old task/card authoring is legacy: [convert before continuing](legacy-transition.md).

- [Specifications and individual requirements](forms-product.md).
- [Lean work entries and result artifacts](forms-technical.md).
- [Shared choices, technical and architectural decisions](forms-decisions.md).
- [Navigation, queues, and settings](forms-navigation.md).
- [One-shot migration coverage](forms-migration.md).
- [Incoming bugs, research, and ideas](forms-intake.md).
- [Optional findings register](forms-findings.md).

## Before creating a document

Select [documentation purpose and ownership](documentation.md#documentation-purpose-and-ownership)
for descriptions, references, guides/procedures, obligations, work context, and results.
Those materials need no universal R/Q record or a separate form for every document type.
Check for an existing canonical owner. Choose one independently useful contract/question/
result; an inline section or queue entry can suffice. Preserve descriptive filenames,
stable IDs, project language, and real links. Do not generate placeholder files as backlog
or reintroduce PRD/layer cards from an old form.

## Completed-form checks

- Requirement and work IDs are unique/stable; references resolve.
- Applicability, acceptance, and current versus historical state are unambiguous.
- Queue/index context stays concise; explanation/summaries link their canonical sources
  without creating competing normative contracts or work states.
- Each work item has one canonical state and meaningful result boundary; concrete waits
  cross queue files correctly and do not create self/cyclic blocking.
- Completed/cancelled results remain visible with honest verification limits.
- New choices have acceptance; implementation reconciles the preserved contracts.
- Converted legacy sources point to self-contained new owners; repeat conversion reuses them.
- Full migration covers all agreed source ranges; scoped work does not claim full migration.
- Actual available checks passed; lint does not substitute for semantic/source comparison.

Examples are illustrative, not accepted project choices or records to create automatically.
