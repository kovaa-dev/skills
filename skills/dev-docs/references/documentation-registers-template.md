# Card and navigation forms

Choose one required form; do not load every example. The rules are in the
[documentation governance](documentation.md) and [tracker](task-tracker.md).

- [Product task](forms-product.md).
- [Technical task](forms-technical.md).
- [Technical and architectural decisions](forms-decisions.md).
- [Navigation and settings](forms-navigation.md).
- [Source coverage and findings](forms-evidence.md).
- [Incoming bugs, findings, and ideas](forms-intake.md).

## Granularity check before creating a file

Apply the “Granularity of any document” section of the [governance](documentation.md).
Choose one outcome/question/contract and check that there is no canonical duplicate.
State boundaries and required inputs; create a separate card for a related independent outcome
that meets the registration threshold for tracking rather than making it a giant
subtask. For navigation, use links labeled by purpose; the task index shows
the mandatory compact status projection but does not replicate owner/acceptance/progress
or another contract in overview headers.
Test the reading route with one typical task: are unrelated neighboring
topics required, and can they be replaced with precise links/named sections without losing
mandatory invariants? This also applies to free-form documents outside these forms.

## Completed-form checks

- All IDs are unique and stable, placeholders have been replaced, and links exist.
- Dependencies have the correct type and do not form cycles.
- Assigned work, accepted deferred work, and unresolved independently actionable/high-risk
  work that meets the tracker's registration threshold has cards; other ideas
  have not automatically become backlog items.
- Every registered task is visible exactly once in the task index: an active task appears in
  the current/future delivery group, while `done`/`cancelled` appears in the last assigned group
  or `History`; standard stages are not imposed on an existing project.
- Each task's status projection matches its canonical card;
  owner/acceptance/progress are not replicated across indexes and assignments.
- In audit/migration decomposition, parallel-ready tasks have explicit prerequisites and independent outcomes; hidden shared boundaries become an integration task only when they have their own acceptance.
- Accepted decisions were actually accepted; done has verified evidence and applicable
  closure reconciliation with the current canonical contract.
- For a full/large move, temporary source mapping and a checkpoint make coverage verifiable;
  a routine card and small migration do not require a separate map. After
  completion, mapping is collapsed or retained only as explicitly required historical evidence.
- Checks from the bootstrap guide have been adapted; lint does not replace semantic review.
