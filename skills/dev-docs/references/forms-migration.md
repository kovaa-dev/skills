# Requirement and queue migration coverage

Use [one-shot migration](governance-migration.md) for a full selected scope and
[on-touch conversion](legacy-transition.md) for ordinary work. The former task-schema
migration is legacy; the destination is always specifications, queues, and results.

Use the shared [coverage protocol](legacy-transition.md#coverage-and-reconciliation).
A small conversion keeps the same accounting inline in the old-source notice or work result;
a detailed temporary table is for full/large migration or required traceability.
Rows identify meaningful units/conditions, not merely filenames; group only when each
contributing meaning and destination remains checkable.

```md
# Migration coverage

| Source/baseline/range or new input | Meaning unit/type | Canonical destination and revision | Disposition/reason | Check or remaining gap |
| --- | --- | --- | --- | --- |
| <exact source unit/version, including relevant exception/condition> | <short semantic label, no copied contract> | <R/revision, decision/question, documentation, Q/result/history locator> | <captured/shared/historical/residual; accepted reason where needed> | <two-way meaning check or exact unresolved source/question> |
| <new input source/date during work> | <new/changed obligation or pending question> | <updated/new canonical locator and state> | <captured/proposed/question; do not attribute it to the old baseline> | <capture check or next needed answer> |

## Recoverability and completion

- Preserved source: <immutable revision, exact copy, or patch>.
- Current scope: <checked baseline/ranges and acceptance>.
- New/changed inputs: <sources and canonical destinations, or none identified>.
- Remaining: <unconverted/unread/unmapped ranges, conflicts, or unavailable sources>.
- Verification: <forward/reverse meaning checks, source delta, links, graph, and history checks actually completed>.
- Final location: <checked mapping/baseline/dispositions in the condensed result or linked history>.
```

Source-to-destination mapping must account for questions, exceptions, dependencies,
and completed/cancelled outcomes, not merely renamed files. Repeated entry reuses existing
destinations. A partial-source notice identifies converted ranges and residual active
legacy sections under [on-touch conversion](legacy-transition.md#convert-before-continuing).
Do not mark open/unmapped material migrated or preserve a permanent second
tracker. Cleanup/deletion follows explicit authority and verified recovery.
